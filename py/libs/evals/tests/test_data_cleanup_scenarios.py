<<<<<<< HEAD
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
=======
"""Tests for data cleanup evaluation scenarios."""

from ms.evals_core.scenarios.data_cleanup import get_scenarios


class TestDataCleanupScenarios:
    """Verify that all data cleanup scenarios are well-formed."""

    def test_returns_scenarios(self) -> None:
        scenarios = get_scenarios()
        assert len(scenarios) > 0, "No data cleanup scenarios returned"

    def test_all_scenario_ids_unique(self) -> None:
        scenarios = get_scenarios()
        ids = [s.scenario_id for s in scenarios]
        assert len(ids) == len(set(ids)), f"Duplicate IDs: {[x for x in ids if ids.count(x) > 1]}"

    def test_all_scenarios_have_required_fields(self) -> None:
        scenarios = get_scenarios()
        for s in scenarios:
            assert s.subject, f"{s.scenario_id}: empty subject"
            assert s.description, f"{s.scenario_id}: empty description"
            assert s.reporter_name, f"{s.scenario_id}: empty reporter_name"
            assert s.reporter_email, f"{s.scenario_id}: empty reporter_email"
            assert s.reporter_department, f"{s.scenario_id}: empty reporter_department"
            assert s.next_best_action, f"{s.scenario_id}: empty next_best_action"
            assert len(s.remediation_steps) > 0, f"{s.scenario_id}: no remediation_steps"

    def test_all_scenarios_have_tags(self) -> None:
        scenarios = get_scenarios()
        for s in scenarios:
            assert len(s.tags) > 0, f"{s.scenario_id}: no tags"
            assert "data-cleanup" in s.tags, f"{s.scenario_id}: missing 'data-cleanup' tag"

    def test_scenarios_convert_to_scenario_model(self) -> None:
        scenarios = get_scenarios()
        for idx, s in enumerate(scenarios):
            scenario = s.to_scenario(f"INC-TEST-{idx:04d}")
            assert scenario.ticket.ticket_id == f"INC-TEST-{idx:04d}"
            assert scenario.gold.ticket_id == f"INC-TEST-{idx:04d}"
            assert scenario.gold.category is not None
            assert scenario.gold.priority is not None
            assert scenario.gold.assigned_team is not None

    def test_known_scenario_ids(self) -> None:
        """Verify expected scenario IDs exist."""
        scenarios = get_scenarios()
        ids = {s.scenario_id for s in scenarios}
        expected = {f"DC-{i:03d}" for i in range(1, 161)}
        assert expected.issubset(ids), f"Missing IDs: {expected - ids}"

    def test_minimum_scenario_count(self) -> None:
        """Data cleanup should have at least 130 scenarios."""
        scenarios = get_scenarios()
        assert len(scenarios) >= 160, f"Expected >= 160 DC scenarios, got {len(scenarios)}"

    def test_covers_key_cleanup_categories(self) -> None:
        """Verify that key data cleanup noise types are covered."""
        scenarios = get_scenarios()
        all_tags = set()
        for s in scenarios:
            all_tags.update(s.tags)

        expected_tags = {
            "long-email",
            "base64",
            "quoted-replies",
            "garbled-text",
            "inline-code",
            "monitoring-alerts",
            "mime-encoded",
            "no-linebreaks",
            "rtf-markup",
            "conflicting-replies",
            "monitoring-metrics",
            "pdf-conversion",
            "massive-cc-list",
            "ocr-layout",
            "speech-to-text",
            "newsletter",
            "pdf-inline",
            "css-noise",
            "xml-soap",
            "sql-dump",
            "markdown-artifacts",
            "multilingual-disclaimer",
            "json-payload",
            "excessive-whitespace",
            "corrupted-headers",
            "vcalendar-noise",
            "hex-dump",
            "double-encoded-html",
            "chat-transcript",
            "registry-dump",
            "http-headers",
            "cid-references",
            "escaped-json",
            "tsv-data",
            "vcard-data",
            "cron-output",
            "concatenated-tickets",
            "all-caps",
            "long-subject",
            "container-logs",
            "k8s-output",
            "emoji-subject",
            "powershell-output",
            "view-source",
            "rtl-text",
            "form-artifacts",
            "event-log",
            "windows-events",
            "packet-capture",
            "tcpdump",
            "ci-pipeline",
            "github-actions",
            "tracking-urls",
            "calendar-forward",
            "ics-spam",
            "spreadsheet-paste",
            "misaligned-columns",
            "ansi-codes",
            "control-characters",
            # New tags from DC-076..DC-090
            "multi-topic",
            "rambling",
            "pdf-embed",
            "inline-binary",
            "screenshot-heavy",
            "autocorrect",
            "typos",
            "mobile-input",
            "voicemail",
            "accent-noise",
            "zero-width-chars",
            "invisible-unicode",
            "auto-translation",
            "translation-artifacts",
            "css-dark-mode",
            "mass-forward",
            "jwt-token",
            "oauth-dump",
            "auth-trace",
            "yaml-config",
            "docker-compose",
            "git-diff",
            "code-paste",
            "multiple-screenshots",
            "data-uri-flood",
            "terse-message",
            "minimal-context",
            "bidi-text",
            "rtl-ltr-mixed",
            "arabic-english",
            "unicode-control",
            # New tags from DC-101..DC-110
            "graphql-introspection",
            "bsod-minidump",
            "webhook-payload",
            "powershell-streams",
            "docker-compose-flood",
            "ocr-number-corruption",
            "quoted-printable-encoding",
            "servicenow-audit-trail",
            "bloomberg-terminal-paste",
            "excel-formula-artifacts",
            # New tags from DC-111..DC-120
            "sql-query-paste",
            "tabular-noise",
            "diagram-text",
            "ascii-art",
            "bsod-dump",
            "crash-stack",
            "k8s-describe",
            "container-events",
            "url-noise",
            "latex-notation",
            "math-formulas",
            "arm-template",
            "json-config-dump",
            "merge-conflict-markers",
            "git-artifacts",
            "macos-crash-report",
            "crash-reporter",
            # New tags from DC-121..DC-130
            "csv-data-inline",
            "long-urls",
            "tracking-parameters",
            "rtf-conversion",
            "document-artifacts",
            "auto-reply-chain",
            "ooo-noise",
            "svg-inline",
            "cross-threaded",
            "interleaved-issues",
            "buried-content",
            "env-var-dump",
            "config-noise",
            "git-diff-noise",
            "merge-conflicts",
            "yaml-config-dump",
            "kubernetes",
            # New tags from DC-151..DC-160
            "very-long-email",
            "base64-flood",
            "base64-encoded-text",
            "giant-signature",
            "deep-quoting",
            "mojibake-severe",
            "json-config-dump",
            "code-switching",
            "url-spam",
            "email-metadata",
        }
        assert expected_tags.issubset(all_tags), f"Missing cleanup tags: {expected_tags - all_tags}"
>>>>>>> users/fde-platform-agent/fde-hiring-test-3/boyevche
