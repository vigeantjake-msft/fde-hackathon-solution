#!/usr/bin/env python3
"""Evaluation tests for data cleanup edge cases.

Tests that the triage system handles noisy, malformed, and degraded input
gracefully — producing valid, correctly classified output regardless of
input quality.

Test categories:
  1. Schema compliance — valid structured output for every degraded input
  2. Classification accuracy — correct triage despite noisy data
  3. Noise resilience — system extracts signal from noisy tickets

Usage:
    cd docs/eval
    python test_data_cleanup.py

    # Or with pytest:
    uv run pytest test_data_cleanup.py -v
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, ".")  # noqa: TID251

from run_eval import CATEGORIES
from run_eval import TEAMS
from run_eval import score_submission
from run_eval import score_ticket

# ── Load datasets ────────────────────────────────────────────────────

_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "tickets"
_TICKETS_PATH = _DATA_DIR / "data_cleanup_eval.json"
_GOLD_PATH = _DATA_DIR / "data_cleanup_eval_gold.json"

_TICKETS: list[dict] = json.loads(_TICKETS_PATH.read_text())
_GOLD: list[dict] = json.loads(_GOLD_PATH.read_text())
_GOLD_BY_ID: dict[str, dict] = {g["ticket_id"]: g for g in _GOLD}

# Valid values from the output schema
_VALID_CATEGORIES = set(CATEGORIES)
_VALID_TEAMS = set(TEAMS)
_VALID_PRIORITIES = {"P1", "P2", "P3", "P4"}
_VALID_MISSING_INFO = {
    "affected_system",
    "error_message",
    "steps_to_reproduce",
    "affected_users",
    "environment_details",
    "timestamp",
    "previous_ticket_id",
    "contact_info",
    "device_info",
    "application_version",
    "network_location",
    "business_impact",
    "reproduction_frequency",
    "screenshot_or_attachment",
    "authentication_method",
    "configuration_details",
}
_REQUIRED_FIELDS = {
    "ticket_id",
    "category",
    "priority",
    "assigned_team",
    "needs_escalation",
    "missing_information",
    "next_best_action",
    "remediation_steps",
}


# ── Dataset integrity tests ──────────────────────────────────────────


def test_dataset_has_15_tickets():
    assert len(_TICKETS) == 15, f"Expected 15 data cleanup tickets, got {len(_TICKETS)}"


def test_gold_has_15_answers():
    assert len(_GOLD) == 15, f"Expected 15 gold answers, got {len(_GOLD)}"


def test_ticket_ids_match():
    ticket_ids = {t["ticket_id"] for t in _TICKETS}
    gold_ids = {g["ticket_id"] for g in _GOLD}
    assert ticket_ids == gold_ids, f"Mismatched IDs: {ticket_ids.symmetric_difference(gold_ids)}"


def test_all_ticket_ids_prefixed():
    for t in _TICKETS:
        assert t["ticket_id"].startswith("INC-DC"), f"Bad ticket_id prefix: {t['ticket_id']}"


def test_gold_categories_valid():
    for g in _GOLD:
        assert g["category"] in _VALID_CATEGORIES, (
            f"{g['ticket_id']}: invalid category '{g['category']}'"
        )


def test_gold_priorities_valid():
    for g in _GOLD:
        assert g["priority"] in _VALID_PRIORITIES, (
            f"{g['ticket_id']}: invalid priority '{g['priority']}'"
        )


def test_gold_teams_valid():
    for g in _GOLD:
        assert g["assigned_team"] in _VALID_TEAMS, (
            f"{g['ticket_id']}: invalid team '{g['assigned_team']}'"
        )


def test_gold_missing_info_valid():
    for g in _GOLD:
        for item in g["missing_information"]:
            assert item in _VALID_MISSING_INFO, (
                f"{g['ticket_id']}: invalid missing_information value '{item}'"
            )


def test_gold_schema_fields():
    for g in _GOLD:
        missing = _REQUIRED_FIELDS - set(g.keys())
        assert not missing, f"{g['ticket_id']}: missing fields {missing}"


# ── Scoring tests (gold vs gold = perfect) ───────────────────────────


def test_perfect_submission_scores_85():
    result = score_submission(_GOLD, _GOLD)
    assert result["classification_score"] == 85.0, (
        f"Perfect submission should score 85.0, got {result['classification_score']}"
    )


def test_perfect_submission_no_errors():
    result = score_submission(_GOLD, _GOLD)
    assert result["tickets_errored"] == 0


def test_each_gold_ticket_scores_perfectly():
    for g in _GOLD:
        scores = score_ticket(dict(g), g)
        assert scores["weighted_total"] > 0.84, (
            f"{g['ticket_id']}: expected weighted_total > 0.84, got {scores['weighted_total']}"
        )


# ── Data-specific edge case tests ────────────────────────────────────


def test_very_long_email_has_valid_gold():
    """INC-DC001: Very long email chain — actual issue is VPN connection timeout."""
    ticket = next(t for t in _TICKETS if t["ticket_id"] == "INC-DC001")
    gold = _GOLD_BY_ID["INC-DC001"]
    assert len(ticket["description"]) > 5000, "Ticket should have very long description"
    assert gold["category"] == "Network & Connectivity"
    assert gold["assigned_team"] == "Network Operations"


def test_base64_image_has_valid_gold():
    """INC-DC002: Base64 image data embedded in email body."""
    ticket = next(t for t in _TICKETS if t["ticket_id"] == "INC-DC002")
    gold = _GOLD_BY_ID["INC-DC002"]
    assert "base64" in ticket["description"].lower(), "Ticket should contain base64 data"
    assert gold["category"] == "Software & Applications"
    assert gold["assigned_team"] == "Enterprise Applications"


def test_html_markup_has_valid_gold():
    """INC-DC003: HTML markup with script tags in ticket body."""
    ticket = next(t for t in _TICKETS if t["ticket_id"] == "INC-DC003")
    gold = _GOLD_BY_ID["INC-DC003"]
    assert "<script>" in ticket["description"] or "<html>" in ticket["description"]
    assert gold["category"] == "Hardware & Peripherals"
    assert gold["assigned_team"] == "Endpoint Engineering"


def test_garbled_transcription_has_valid_gold():
    """INC-DC004: Garbled phone transcription with [inaudible] markers."""
    ticket = next(t for t in _TICKETS if t["ticket_id"] == "INC-DC004")
    gold = _GOLD_BY_ID["INC-DC004"]
    assert ticket["description"].count("[inaudible]") >= 5
    assert gold["category"] == "Data & Storage"
    assert gold["assigned_team"] == "Data Platform"


def test_emoji_heavy_has_valid_gold():
    """INC-DC005: Ticket body heavily laden with emoji."""
    ticket = next(t for t in _TICKETS if t["ticket_id"] == "INC-DC005")
    gold = _GOLD_BY_ID["INC-DC005"]
    assert "💻" in ticket["description"]
    assert gold["category"] == "Hardware & Peripherals"
    assert gold["assigned_team"] == "Endpoint Engineering"


def test_empty_ticket_has_valid_gold():
    """INC-DC006: Completely empty subject and description."""
    ticket = next(t for t in _TICKETS if t["ticket_id"] == "INC-DC006")
    gold = _GOLD_BY_ID["INC-DC006"]
    assert ticket["subject"] == ""
    assert ticket["description"] == ""
    assert gold["category"] == "Not a Support Ticket"
    assert gold["assigned_team"] == "None"


def test_deep_forwarding_chain_has_valid_gold():
    """INC-DC007: Deeply nested RE:/FW: forwarding chain."""
    ticket = next(t for t in _TICKETS if t["ticket_id"] == "INC-DC007")
    gold = _GOLD_BY_ID["INC-DC007"]
    assert ticket["subject"].count("RE:") >= 4
    assert gold["category"] == "Software & Applications"
    assert gold["assigned_team"] == "Enterprise Applications"


def test_excessive_whitespace_has_valid_gold():
    """INC-DC008: Excessive whitespace and formatting throughout."""
    ticket = next(t for t in _TICKETS if t["ticket_id"] == "INC-DC008")
    gold = _GOLD_BY_ID["INC-DC008"]
    assert "     " in ticket["description"]
    assert gold["category"] == "Network & Connectivity"
    assert gold["assigned_team"] == "Network Operations"


def test_mixed_language_has_valid_gold():
    """INC-DC009: Mixed Spanish/English ticket body."""
    ticket = next(t for t in _TICKETS if t["ticket_id"] == "INC-DC009")
    gold = _GOLD_BY_ID["INC-DC009"]
    assert "Buenos días" in ticket["description"]
    assert gold["category"] == "Software & Applications"
    assert gold["assigned_team"] == "Enterprise Applications"


def test_url_spam_phishing_report_has_valid_gold():
    """INC-DC010: Many suspicious URLs — user reporting phishing."""
    ticket = next(t for t in _TICKETS if t["ticket_id"] == "INC-DC010")
    gold = _GOLD_BY_ID["INC-DC010"]
    assert ticket["description"].count("http") >= 5
    assert gold["category"] == "Security & Compliance"
    assert gold["assigned_team"] == "Security Operations"
    assert gold["needs_escalation"] is True


def test_code_blocks_in_ticket_has_valid_gold():
    """INC-DC011: Code blocks and JSON formatting in ticket body."""
    ticket = next(t for t in _TICKETS if t["ticket_id"] == "INC-DC011")
    gold = _GOLD_BY_ID["INC-DC011"]
    assert "```" in ticket["description"]
    assert gold["category"] == "Data & Storage"
    assert gold["assigned_team"] == "Data Platform"


def test_repeated_text_has_valid_gold():
    """INC-DC012: Repeated/stuck keyboard text followed by actual issue."""
    ticket = next(t for t in _TICKETS if t["ticket_id"] == "INC-DC012")
    gold = _GOLD_BY_ID["INC-DC012"]
    assert ticket["description"].count("account issue") >= 10
    assert gold["category"] == "Access & Authentication"
    assert gold["assigned_team"] == "Identity & Access Management"


def test_pii_mention_has_valid_gold():
    """INC-DC013: Ticket mentioning that PII was previously included."""
    ticket = next(t for t in _TICKETS if t["ticket_id"] == "INC-DC013")
    gold = _GOLD_BY_ID["INC-DC013"]
    assert "SSN" in ticket["description"]
    assert gold["category"] == "General Inquiry"
    assert gold["assigned_team"] == "Endpoint Engineering"


def test_mixed_french_english_has_valid_gold():
    """INC-DC014: Mixed French/English ticket about file share access."""
    ticket = next(t for t in _TICKETS if t["ticket_id"] == "INC-DC014")
    gold = _GOLD_BY_ID["INC-DC014"]
    assert "Bonjour" in ticket["description"]
    assert gold["category"] == "Data & Storage"
    assert gold["assigned_team"] == "Data Platform"


def test_control_characters_in_subject_has_valid_gold():
    """INC-DC015: Tab and other formatting characters in subject line."""
    gold = _GOLD_BY_ID["INC-DC015"]
    assert gold["category"] == "Data & Storage"
    assert gold["assigned_team"] == "Data Platform"


# ── Robustness property tests ────────────────────────────────────────


def test_all_tickets_have_required_input_fields():
    """Every ticket must have the fields from input.json schema."""
    required = {"ticket_id", "subject", "description", "reporter", "created_at", "channel"}
    for t in _TICKETS:
        missing = required - set(t.keys())
        assert not missing, f"{t['ticket_id']}: missing input fields {missing}"


def test_all_reporters_have_required_fields():
    """Every reporter must have name, email, department."""
    for t in _TICKETS:
        reporter = t["reporter"]
        for field in ("name", "email", "department"):
            assert field in reporter, f"{t['ticket_id']}: reporter missing {field}"


def test_gold_escalation_is_boolean():
    """needs_escalation must be a proper boolean, not a string."""
    for g in _GOLD:
        assert isinstance(g["needs_escalation"], bool), (
            f"{g['ticket_id']}: needs_escalation is {type(g['needs_escalation'])}, expected bool"
        )


def test_gold_missing_info_is_list():
    """missing_information must be a list."""
    for g in _GOLD:
        assert isinstance(g["missing_information"], list), (
            f"{g['ticket_id']}: missing_information is {type(g['missing_information'])}, expected list"
        )


def test_gold_remediation_steps_is_list():
    """remediation_steps must be a non-empty list."""
    for g in _GOLD:
        assert isinstance(g["remediation_steps"], list), (
            f"{g['ticket_id']}: remediation_steps is {type(g['remediation_steps'])}, expected list"
        )
        assert len(g["remediation_steps"]) > 0, (
            f"{g['ticket_id']}: remediation_steps should not be empty"
        )


def test_not_a_support_ticket_routed_to_none():
    """Tickets classified as 'Not a Support Ticket' must route to 'None'."""
    for g in _GOLD:
        if g["category"] == "Not a Support Ticket":
            assert g["assigned_team"] == "None", (
                f"{g['ticket_id']}: 'Not a Support Ticket' should route to 'None', "
                f"got '{g['assigned_team']}'"
            )


def test_none_team_only_for_non_support():
    """Team 'None' should only be used for 'Not a Support Ticket' category."""
    for g in _GOLD:
        if g["assigned_team"] == "None":
            assert g["category"] == "Not a Support Ticket", (
                f"{g['ticket_id']}: team 'None' should only be used with "
                f"'Not a Support Ticket', got category '{g['category']}'"
            )


# ── Runner ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
            print(f"  ✓ {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"  ✗ {t.__name__}: {e}")
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
