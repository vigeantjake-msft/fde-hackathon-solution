# Copyright (c) Microsoft. All rights reserved.
"""Tests for data cleanup evaluation scenarios.

Validates that all data cleanup scenarios are well-formed, use valid
enum values, and cover the expected range of data quality challenges.
"""

import re

from ms.evals.models.scenario import EvalScenario
from ms.evals.models.scenario import ScenarioCategory

_EXPECTED_TICKET_IDS = {f"INC-{5001 + i}" for i in range(15)}
_EXPECTED_SCENARIO_IDS = {f"dc-{i:03d}" for i in range(1, 16)}

_EXPECTED_SUBCATEGORIES = {
    "long_email_thread",
    "base64_image_inline",
    "html_markup_body",
    "long_email_signature",
    "deep_forwarded_chain",
    "garbled_encoding",
    "pasted_log_data",
    "excessive_emojis",
    "duplicated_content",
    "auto_generated_alert",
    "url_spam_tracking",
    "mixed_languages",
    "extremely_terse",
    "json_error_dump",
    "email_metadata_noise",
}


def test_scenario_count(data_cleanup_scenarios: list[EvalScenario]) -> None:
    """There should be exactly 15 data cleanup scenarios."""
    assert len(data_cleanup_scenarios) == 15


def test_all_scenario_ids_present(data_cleanup_scenarios: list[EvalScenario]) -> None:
    """All expected scenario IDs should be registered."""
    actual_ids = {s.metadata.scenario_id for s in data_cleanup_scenarios}
    assert actual_ids == _EXPECTED_SCENARIO_IDS


def test_all_ticket_ids_present(data_cleanup_scenarios: list[EvalScenario]) -> None:
    """All expected ticket IDs (INC-5001 through INC-5015) should be present."""
    actual_ids = {s.ticket.ticket_id for s in data_cleanup_scenarios}
    assert actual_ids == _EXPECTED_TICKET_IDS


def test_ticket_id_matches_expected(data_cleanup_scenarios: list[EvalScenario]) -> None:
    """Each scenario's ticket_id must match between ticket and expected triage."""
    for scenario in data_cleanup_scenarios:
        assert scenario.ticket.ticket_id == scenario.expected.ticket_id


def test_all_categories_are_data_cleanup(data_cleanup_scenarios: list[EvalScenario]) -> None:
    """All scenarios should be in the DATA_CLEANUP category."""
    for scenario in data_cleanup_scenarios:
        assert scenario.metadata.category == ScenarioCategory.DATA_CLEANUP


def test_subcategory_coverage(data_cleanup_scenarios: list[EvalScenario]) -> None:
    """All expected subcategories should be represented."""
    actual_subcategories = {s.metadata.subcategory for s in data_cleanup_scenarios}
    assert actual_subcategories == _EXPECTED_SUBCATEGORIES


def test_ticket_id_format(data_cleanup_scenarios: list[EvalScenario]) -> None:
    """All ticket IDs should match the INC-NNNN format."""
    for scenario in data_cleanup_scenarios:
        assert re.match(r"^INC-\d+$", scenario.ticket.ticket_id)


def test_descriptions_non_empty(data_cleanup_scenarios: list[EvalScenario]) -> None:
    """All ticket descriptions should have substantive content."""
    for scenario in data_cleanup_scenarios:
        assert len(scenario.ticket.description) > 10, f"{scenario.ticket.ticket_id} has too short a description"


def test_expected_has_remediation_steps(data_cleanup_scenarios: list[EvalScenario]) -> None:
    """All expected triage decisions should include at least one remediation step."""
    for scenario in data_cleanup_scenarios:
        assert len(scenario.expected.remediation_steps) >= 1, (
            f"{scenario.ticket.ticket_id} missing remediation steps"
        )


def test_expected_has_next_best_action(data_cleanup_scenarios: list[EvalScenario]) -> None:
    """All expected triage decisions should include a next_best_action."""
    for scenario in data_cleanup_scenarios:
        assert len(scenario.expected.next_best_action) > 10, (
            f"{scenario.ticket.ticket_id} has too short a next_best_action"
        )


def test_metadata_has_description_and_challenge(data_cleanup_scenarios: list[EvalScenario]) -> None:
    """All scenario metadata should have a description and challenge string."""
    for scenario in data_cleanup_scenarios:
        assert len(scenario.metadata.description) > 10
        assert len(scenario.metadata.challenge) > 10


def test_no_duplicate_ticket_ids(data_cleanup_scenarios: list[EvalScenario]) -> None:
    """No two scenarios should share the same ticket_id."""
    ticket_ids = [s.ticket.ticket_id for s in data_cleanup_scenarios]
    assert len(ticket_ids) == len(set(ticket_ids))


def test_reporter_email_is_contoso(data_cleanup_scenarios: list[EvalScenario]) -> None:
    """All reporter emails should be @contoso.com."""
    for scenario in data_cleanup_scenarios:
        assert scenario.ticket.reporter.email.endswith("@contoso.com"), (
            f"{scenario.ticket.ticket_id} reporter email is not @contoso.com"
        )
