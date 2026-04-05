# Copyright (c) Microsoft. All rights reserved.
"""Tests for data cleanup evaluation scenarios.

Validates that all scenarios are well-formed, have unique IDs,
use valid enum values, and match ticket_id between ticket and gold.
"""

from ms.evals_core.scenarios.data_cleanup import get_data_cleanup_scenarios

_SCENARIOS = get_data_cleanup_scenarios()


class TestDataCleanupScenariosStructure:
    """Structural validation for all data cleanup scenarios."""

    def test_scenarios_not_empty(self) -> None:
        assert len(_SCENARIOS) > 0, "Expected at least one data cleanup scenario"

    def test_all_scenarios_are_data_cleanup(self) -> None:
        for scenario in _SCENARIOS:
            assert scenario.scenario_category == "data_cleanup", (
                f"Scenario {scenario.ticket.ticket_id} has wrong category: {scenario.scenario_category}"
            )

    def test_ticket_ids_are_unique(self) -> None:
        ids = [s.ticket.ticket_id for s in _SCENARIOS]
        assert len(ids) == len(set(ids)), f"Duplicate ticket IDs found: {[x for x in ids if ids.count(x) > 1]}"

    def test_ticket_id_matches_gold(self) -> None:
        for scenario in _SCENARIOS:
            assert scenario.ticket.ticket_id == scenario.gold.ticket_id, (
                f"Ticket ID mismatch: ticket={scenario.ticket.ticket_id}, gold={scenario.gold.ticket_id}"
            )

    def test_scenario_tags_are_unique(self) -> None:
        tags = [s.scenario_tag for s in _SCENARIOS]
        assert len(tags) == len(set(tags)), f"Duplicate tags found: {[x for x in tags if tags.count(x) > 1]}"

    def test_gold_has_remediation_steps(self) -> None:
        for scenario in _SCENARIOS:
            assert len(scenario.gold.remediation_steps) >= 1, (
                f"Scenario {scenario.ticket.ticket_id} has no remediation steps"
            )

    def test_gold_has_next_best_action(self) -> None:
        for scenario in _SCENARIOS:
            assert len(scenario.gold.next_best_action) > 10, (
                f"Scenario {scenario.ticket.ticket_id} has a trivial next_best_action"
            )

    def test_scenario_descriptions_are_nonempty(self) -> None:
        for scenario in _SCENARIOS:
            assert len(scenario.description) > 10, (
                f"Scenario {scenario.ticket.ticket_id} has a trivial description"
            )


class TestDataCleanupScenarioContent:
    """Content-level checks for specific scenario categories."""

    def test_long_email_thread_is_long(self) -> None:
        long_threads = [s for s in _SCENARIOS if s.scenario_tag == "long_email_thread"]
        assert len(long_threads) == 1
        assert len(long_threads[0].ticket.description) > 1000

    def test_base64_image_contains_data_uri(self) -> None:
        b64_scenarios = [s for s in _SCENARIOS if "base64" in s.scenario_tag]
        assert len(b64_scenarios) >= 1
        for scenario in b64_scenarios:
            desc = scenario.ticket.description
            assert "base64" in desc.lower() or "Base64" in desc

    def test_html_body_contains_html_tags(self) -> None:
        html_scenarios = [s for s in _SCENARIOS if s.scenario_tag == "html_email_body"]
        assert len(html_scenarios) == 1
        assert "<html>" in html_scenarios[0].ticket.description

    def test_garbled_encoding_has_mojibake(self) -> None:
        garbled = [s for s in _SCENARIOS if s.scenario_tag == "garbled_encoding"]
        assert len(garbled) == 1
        # Check for common UTF-8 mojibake patterns
        desc = garbled[0].ticket.description
        assert "Ã" in desc

    def test_unicode_emoji_has_emojis(self) -> None:
        emoji_scenarios = [s for s in _SCENARIOS if s.scenario_tag == "unicode_emoji_overload"]
        assert len(emoji_scenarios) == 1
        desc = emoji_scenarios[0].ticket.description
        assert "🚨" in desc or "😡" in desc

    def test_json_xml_dump_has_json(self) -> None:
        json_scenarios = [s for s in _SCENARIOS if s.scenario_tag == "json_xml_dump"]
        assert len(json_scenarios) == 1
        desc = json_scenarios[0].ticket.description
        assert '"error"' in desc or "SalesOrder" in desc

    def test_terse_ticket_is_short(self) -> None:
        terse = [s for s in _SCENARIOS if s.scenario_tag == "extremely_terse"]
        assert len(terse) == 1
        assert len(terse[0].ticket.description) < 50

    def test_zero_width_characters_present(self) -> None:
        zw_scenarios = [s for s in _SCENARIOS if s.scenario_tag == "zero_width_characters"]
        assert len(zw_scenarios) == 1
        desc = zw_scenarios[0].ticket.description
        assert "\u200b" in desc or "\u200c" in desc or "\u200d" in desc

    def test_quoted_printable_has_encoded_sequences(self) -> None:
        qp_scenarios = [s for s in _SCENARIOS if s.scenario_tag == "quoted_printable_encoding"]
        assert len(qp_scenarios) == 1
        desc = qp_scenarios[0].ticket.description
        assert "=0D=0A" in desc

    def test_massive_wall_of_text_is_long(self) -> None:
        wall = [s for s in _SCENARIOS if s.scenario_tag == "massive_wall_of_text"]
        assert len(wall) == 1
        assert len(wall[0].ticket.description) > 3000
        assert "\n" not in wall[0].ticket.description

    def test_rtf_artifacts_has_rtf_codes(self) -> None:
        rtf = [s for s in _SCENARIOS if s.scenario_tag == "rtf_formatting_artifacts"]
        assert len(rtf) == 1
        desc = rtf[0].ticket.description
        assert r"\rtf1" in desc

    def test_multiple_inline_images_has_multiple_data_uris(self) -> None:
        multi = [s for s in _SCENARIOS if s.scenario_tag == "multiple_inline_images"]
        assert len(multi) == 1
        desc = multi[0].ticket.description
        assert desc.count("data:image/") >= 3

    def test_calendar_invite_has_vcalendar(self) -> None:
        cal = [s for s in _SCENARIOS if s.scenario_tag == "calendar_invite_paste"]
        assert len(cal) == 1
        desc = cal[0].ticket.description
        assert "BEGIN:VCALENDAR" in desc
        assert "END:VCALENDAR" in desc

    def test_sql_stack_trace_has_exception(self) -> None:
        sql = [s for s in _SCENARIOS if s.scenario_tag == "sql_stack_trace_dump"]
        assert len(sql) == 1
        desc = sql[0].ticket.description
        assert "SqlException" in desc
        assert "StackTrace" in desc or "at " in desc

    def test_excessive_whitespace_has_tabs(self) -> None:
        ws = [s for s in _SCENARIOS if s.scenario_tag == "excessive_whitespace_formatting"]
        assert len(ws) == 1
        desc = ws[0].ticket.description
        assert "\t\t\t" in desc

    def test_minimum_scenario_count(self) -> None:
        """Ensure we have a comprehensive set of scenarios."""
        assert len(_SCENARIOS) >= 24
