"""Tests for triage.py — response parser and run_triage integration."""

from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest

from models import Category
from models import MissingInfo
from models import Team
from triage import SYSTEM_PROMPT
from triage import TriageLLMOutput
from triage import _parse_llm_output
from triage import run_triage


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_ticket(
    ticket_id: str = "SIG-0001",
    subject: str = "Test subject",
    description: str = "Test description",
    department: str = "Engineering",
    channel: str = "bridge_terminal",
    attachments: list | None = None,
):
    """Build a TriageRequest via the FastAPI model."""
    from models import Reporter
    from models import TriageRequest

    return TriageRequest(
        ticket_id=ticket_id,
        subject=subject,
        description=description,
        reporter=Reporter(
            name="Test User",
            email="test@cdss.space",
            department=department,
        ),
        created_at="2026-01-01T00:00:00Z",
        channel=channel,
        attachments=attachments or [],
    )


def _llm_response(content: str) -> MagicMock:
    """Build a mock LLM response wrapping the given text."""
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


# ---------------------------------------------------------------------------
# _parse_llm_output — pure function, no I/O
# ---------------------------------------------------------------------------


class TestParseLlmOutput:
    """_parse_llm_output coerces raw LLM dicts into validated TriageResponse objects."""

    def test_full_valid_response(self):
        raw: TriageLLMOutput = {
            "category": "Communications & Navigation",
            "priority": "P3",
            "assigned_team": "Deep Space Communications",
            "needs_escalation": False,
            "missing_information": [],
            "next_best_action": "Check the relay.",
            "remediation_steps": ["Step 1", "Step 2"],
        }
        result = _parse_llm_output(raw, "SIG-0001")

        assert result.ticket_id == "SIG-0001"
        assert result.category == Category.COMMS
        assert result.priority == "P3"
        assert result.assigned_team == Team.COMMS
        assert result.needs_escalation is False
        assert result.missing_information == []

    def test_invalid_category_falls_back_to_briefing(self):
        raw: TriageLLMOutput = {"category": "Totally Unknown Category"}
        result = _parse_llm_output(raw, "SIG-X")
        assert result.category == Category.BRIEFING

    def test_invalid_team_falls_back_to_systems(self):
        raw: TriageLLMOutput = {"assigned_team": "Made Up Team"}
        result = _parse_llm_output(raw, "SIG-X")
        assert result.assigned_team == Team.SYSTEMS

    def test_invalid_priority_falls_back_to_p3(self):
        raw: TriageLLMOutput = {"priority": "CRITICAL"}
        result = _parse_llm_output(raw, "SIG-X")
        assert result.priority == "P3"

    def test_priority_is_uppercased_before_validation(self):
        raw: TriageLLMOutput = {"priority": "p1"}
        result = _parse_llm_output(raw, "SIG-X")
        assert result.priority == "P1"

    def test_unknown_missing_info_strings_are_dropped(self):
        raw: TriageLLMOutput = {
            "missing_information": ["affected_subsystem", "made_up_field", "software_version"],
        }
        result = _parse_llm_output(raw, "SIG-X")
        assert MissingInfo.AFFECTED_SUBSYSTEM in result.missing_information
        assert MissingInfo.SOFTWARE_VERSION in result.missing_information
        assert len(result.missing_information) == 2  # made_up_field dropped

    def test_all_valid_missing_info_fields_accepted(self):
        all_fields = [m.value for m in MissingInfo]
        raw: TriageLLMOutput = {"missing_information": all_fields}
        result = _parse_llm_output(raw, "SIG-X")
        assert len(result.missing_information) == len(all_fields)

    def test_missing_escalation_defaults_to_false(self):
        result = _parse_llm_output({}, "SIG-X")
        assert result.needs_escalation is False

    def test_needs_escalation_true(self):
        raw: TriageLLMOutput = {"needs_escalation": True}
        result = _parse_llm_output(raw, "SIG-X")
        assert result.needs_escalation is True

    def test_empty_raw_uses_all_defaults(self):
        result = _parse_llm_output({}, "SIG-EMPTY")
        assert result.ticket_id == "SIG-EMPTY"
        assert result.category == Category.BRIEFING
        assert result.priority == "P3"
        assert result.assigned_team == Team.SYSTEMS
        assert result.needs_escalation is False
        assert result.missing_information == []
        assert result.next_best_action != ""
        assert len(result.remediation_steps) >= 1

    def test_all_valid_categories_parse_correctly(self):
        category_strings = [c.value for c in Category]
        for cat_str in category_strings:
            raw: TriageLLMOutput = {"category": cat_str}
            result = _parse_llm_output(raw, "SIG-X")
            assert result.category.value == cat_str

    def test_all_valid_teams_parse_correctly(self):
        team_strings = [t.value for t in Team]
        for team_str in team_strings:
            raw: TriageLLMOutput = {"assigned_team": team_str}
            result = _parse_llm_output(raw, "SIG-X")
            assert result.assigned_team.value == team_str


# ---------------------------------------------------------------------------
# run_triage — LLM call mocked
# ---------------------------------------------------------------------------


class TestRunTriage:
    """run_triage makes one LLM call and returns a TriageResponse."""

    async def test_returns_correct_category_from_llm(self):
        client = AsyncMock()
        client.chat.completions.create.return_value = _llm_response(
            '{"category": "Communications & Navigation", "priority": "P3",'
            ' "assigned_team": "Deep Space Communications",'
            ' "needs_escalation": false, "missing_information": [],'
            ' "next_best_action": "Check relay.", "remediation_steps": ["Step 1"]}'
        )

        result = await run_triage(_make_ticket(), client)

        assert result.category == Category.COMMS
        assert result.priority == "P3"
        assert result.assigned_team == Team.COMMS

    async def test_ticket_id_is_echoed_from_request(self):
        client = AsyncMock()
        client.chat.completions.create.return_value = _llm_response("{}")

        result = await run_triage(_make_ticket(ticket_id="SIG-9999"), client)

        assert result.ticket_id == "SIG-9999"

    async def test_makes_exactly_one_llm_call(self):
        client = AsyncMock()
        client.chat.completions.create.return_value = _llm_response("{}")

        await run_triage(_make_ticket(), client)

        client.chat.completions.create.assert_called_once()

    async def test_passes_system_prompt_in_messages(self):
        client = AsyncMock()
        client.chat.completions.create.return_value = _llm_response("{}")

        await run_triage(_make_ticket(), client)

        call_kwargs = client.chat.completions.create.call_args.kwargs
        messages = call_kwargs["messages"]
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == SYSTEM_PROMPT

    async def test_ticket_info_appears_in_user_message(self):
        client = AsyncMock()
        client.chat.completions.create.return_value = _llm_response("{}")

        await run_triage(_make_ticket(ticket_id="SIG-FIND-ME"), client)

        call_kwargs = client.chat.completions.create.call_args.kwargs
        user_content = call_kwargs["messages"][1]["content"]
        assert "SIG-FIND-ME" in user_content

    async def test_uses_json_object_response_format(self):
        client = AsyncMock()
        client.chat.completions.create.return_value = _llm_response("{}")

        await run_triage(_make_ticket(), client)

        call_kwargs = client.chat.completions.create.call_args.kwargs
        assert call_kwargs["response_format"] == {"type": "json_object"}

    async def test_survives_empty_llm_response(self):
        """Partial LLM output must not crash the route — defaults are applied."""
        client = AsyncMock()
        client.chat.completions.create.return_value = _llm_response("")

        result = await run_triage(_make_ticket(), client)

        # Defaults applied without raising.
        assert result.priority == "P3"
        assert result.category == Category.BRIEFING

    async def test_propagates_llm_error_after_retries(self):
        from exceptions import LLMError

        client = AsyncMock()
        client.chat.completions.create.side_effect = RuntimeError("Azure down")

        import asyncio
        from unittest.mock import patch

        with patch.object(asyncio, "sleep", new_callable=AsyncMock):
            with pytest.raises(LLMError):
                await run_triage(_make_ticket(), client)
