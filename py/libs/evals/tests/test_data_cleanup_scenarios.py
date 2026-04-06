<<<<<<< HEAD
# Copyright (c) Microsoft. All rights reserved.
"""Tests for data cleanup evaluation scenarios.

Validates that:
1. All data cleanup scenarios are well-formed (valid models)
2. Gold answers use valid enum values from the challenge spec
3. Ticket IDs are unique across all scenarios
4. Scenarios cover the expected range of data quality issues
5. Gold triage responses pass schema validation
"""

import pytest

from ms.evals.constants import CATEGORIES
from ms.evals.constants import MISSING_INFO_VOCABULARY
from ms.evals.constants import PRIORITIES
from ms.evals.constants import TEAMS
from ms.evals.scenarios.base import EvalScenario
from ms.evals.scenarios.data_cleanup import build_data_cleanup_scenarios
from ms.evals.validators.schema_validator import validate_triage_response


class TestDataCleanupScenariosStructure:
    """Validate scenario collection is well-formed."""

    def test_scenarios_not_empty(self, data_cleanup_scenarios: list[EvalScenario]) -> None:
        assert len(data_cleanup_scenarios) >= 15, "Expected at least 15 data cleanup scenarios"

    def test_unique_scenario_ids(self, data_cleanup_scenarios: list[EvalScenario]) -> None:
        ids = [s.scenario_id for s in data_cleanup_scenarios]
        assert len(ids) == len(set(ids)), f"Duplicate scenario IDs found: {ids}"

    def test_unique_ticket_ids(self, data_cleanup_scenarios: list[EvalScenario]) -> None:
        ids = [s.ticket.ticket_id for s in data_cleanup_scenarios]
        assert len(ids) == len(set(ids)), f"Duplicate ticket IDs found: {ids}"

    def test_all_categorized_as_data_cleanup(self, data_cleanup_scenarios: list[EvalScenario]) -> None:
        for s in data_cleanup_scenarios:
            assert s.category == "data_cleanup", (
                f"{s.scenario_id}: expected category='data_cleanup', got {s.category!r}"
            )


class TestDataCleanupGoldAnswers:
    """Validate gold answers use valid enum values."""

    @pytest.fixture(autouse=True)
    def _load_scenarios(self, data_cleanup_scenarios: list[EvalScenario]) -> None:
        self.scenarios = data_cleanup_scenarios

    def test_gold_categories_valid(self) -> None:
        for s in self.scenarios:
            assert s.expected.category in CATEGORIES, f"{s.scenario_id}: invalid gold category {s.expected.category!r}"

    def test_gold_priorities_valid(self) -> None:
        for s in self.scenarios:
            assert s.expected.priority in PRIORITIES, f"{s.scenario_id}: invalid gold priority {s.expected.priority!r}"

    def test_gold_teams_valid(self) -> None:
        for s in self.scenarios:
            assert s.expected.assigned_team in TEAMS, f"{s.scenario_id}: invalid gold team {s.expected.assigned_team!r}"

    def test_gold_missing_info_valid(self) -> None:
        for s in self.scenarios:
            for item in s.expected.missing_information:
                assert item in MISSING_INFO_VOCABULARY, f"{s.scenario_id}: invalid missing info item {item!r}"

    def test_gold_ticket_id_matches(self) -> None:
        for s in self.scenarios:
            assert s.ticket.ticket_id == s.expected.ticket_id, (
                f"{s.scenario_id}: ticket_id mismatch: {s.ticket.ticket_id} != {s.expected.ticket_id}"
            )

    def test_gold_has_remediation_steps(self) -> None:
        for s in self.scenarios:
            assert len(s.expected.remediation_steps) >= 1, (
                f"{s.scenario_id}: gold answer must have at least one remediation step"
            )

    def test_gold_has_next_best_action(self) -> None:
        for s in self.scenarios:
            assert len(s.expected.next_best_action.strip()) > 0, (
                f"{s.scenario_id}: gold answer must have a non-empty next_best_action"
            )


class TestDataCleanupSchemaCompliance:
    """Validate gold answers pass schema validation when serialized."""

    def test_gold_passes_schema_validation(self, data_cleanup_scenarios: list[EvalScenario]) -> None:
        for s in data_cleanup_scenarios:
            response_dict = s.expected.model_dump()
            violations = validate_triage_response(response_dict)
            assert violations == [], (
                f"{s.scenario_id}: schema violations in gold answer: {[str(v) for v in violations]}"
            )


class TestDataCleanupCoverage:
    """Validate scenarios cover the expected range of data quality issues."""

    def test_covers_long_description(self) -> None:
        scenarios = build_data_cleanup_scenarios()
        long_desc = [s for s in scenarios if len(s.ticket.description) > 3000]
        assert len(long_desc) >= 1, "Expected at least one scenario with description > 3000 chars"

    def test_covers_base64_content(self) -> None:
        scenarios = build_data_cleanup_scenarios()
        b64 = [s for s in scenarios if "base64" in s.ticket.description.lower()]
        assert len(b64) >= 1, "Expected at least one scenario with base64 content"

    def test_covers_html_content(self) -> None:
        scenarios = build_data_cleanup_scenarios()
        html = [s for s in scenarios if "<" in s.ticket.description and ">" in s.ticket.description]
        assert len(html) >= 1, "Expected at least one scenario with HTML content"

    def test_covers_empty_or_minimal_input(self) -> None:
        scenarios = build_data_cleanup_scenarios()
        empty = [s for s in scenarios if len(s.ticket.description.strip()) <= 1]
        assert len(empty) >= 1, "Expected at least one scenario with empty/minimal description"

    def test_covers_unicode_content(self) -> None:
        scenarios = build_data_cleanup_scenarios()
        # Check for non-ASCII characters
        unicode_scenarios = [s for s in scenarios if any(ord(c) > 127 for c in s.ticket.description)]
        assert len(unicode_scenarios) >= 1, "Expected at least one scenario with Unicode content"

    def test_covers_garbled_transcription(self) -> None:
        scenarios = build_data_cleanup_scenarios()
        garbled = [s for s in scenarios if "inaudible" in s.ticket.description.lower()]
        assert len(garbled) >= 1, "Expected at least one scenario with garbled transcription"

    def test_covers_email_threads(self) -> None:
        scenarios = build_data_cleanup_scenarios()
        threads = [s for s in scenarios if "forwarded" in s.ticket.description.lower()]
        assert len(threads) >= 1, "Expected at least one scenario with email thread"

    def test_covers_control_characters(self) -> None:
        scenarios = build_data_cleanup_scenarios()
        ctrl = [s for s in scenarios if any(ord(c) < 32 and c not in "\n\r\t" for c in s.ticket.description)]
        assert len(ctrl) >= 1, "Expected at least one scenario with control characters"


class TestDataCleanupTicketValidity:
    """Validate that scenario tickets themselves are well-formed input."""

    def test_tickets_have_valid_channel(self, data_cleanup_scenarios: list[EvalScenario]) -> None:
        valid_channels = {"email", "chat", "portal", "phone"}
        for s in data_cleanup_scenarios:
            assert s.ticket.channel in valid_channels, f"{s.scenario_id}: invalid channel {s.ticket.channel!r}"

    def test_tickets_have_nonempty_subject(self, data_cleanup_scenarios: list[EvalScenario]) -> None:
        for s in data_cleanup_scenarios:
            assert len(s.ticket.subject.strip()) > 0, f"{s.scenario_id}: ticket must have a non-empty subject"

    def test_tickets_have_reporter_info(self, data_cleanup_scenarios: list[EvalScenario]) -> None:
        for s in data_cleanup_scenarios:
            assert len(s.ticket.reporter.name.strip()) > 0, f"{s.scenario_id}: reporter name is empty"
            assert "@" in s.ticket.reporter.email, f"{s.scenario_id}: reporter email missing @"
            assert len(s.ticket.reporter.department.strip()) > 0, f"{s.scenario_id}: reporter dept is empty"
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
        expected = {f"DC-{i:03d}" for i in range(1, 261)}
        assert expected.issubset(ids), f"Missing IDs: {expected - ids}"

    def test_minimum_scenario_count(self) -> None:
        """Data cleanup should have at least 260 scenarios."""
        scenarios = get_scenarios()
        assert len(scenarios) >= 260, f"Expected >= 260 DC scenarios, got {len(scenarios)}"

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
            "code-switching",
            "url-spam",
            "email-metadata",
            # New tags from DC-221..DC-235
            "csv-injection",
            "pgp-signed-email",
            "zalgo-unicode",
            "combining-diacritics",
            "deep-nested-json",
            "sql-output-noise",
            "smime-signature",
            "empty-body",
            "mobile-signature-only",
            "jira-notification",
            "transition-history-noise",
            "registry-export",
            "reg-file-noise",
            "deep-traceback",
            "long-url",
            "query-param-overflow",
            "base64-binary-inline",
            "iac-template-dump",
            "git-blame-output",
            "source-code-noise",
            # New tags from DC-246..DC-260
            "base64-image-flood",
            "ooo-stack",
            "legal-disclaimer",
            "multilingual-footer",
            "teams-transcript",
            "chat-paste",
            "http-dump",
            "response-headers",
            "inline-screenshots",
            "multi-ticket-reference",
            "thread-confusion",
            "servicedesk-template",
            "auto-notification",
            "mojibake-corruption",
            "encoding-mismatch",
            "soap-fault-dump",
            "xml-response",
            "html-table-noise",
            "inline-css-dump",
            "extremely-verbose-buried",
            "rambling-email",
            "embedded-eml",
            "rfc822-headers",
            "ocr-scan-noise",
            "recognition-errors",
            "winrm-transcript",
            "remote-session-dump",
        }
        assert expected_tags.issubset(all_tags), f"Missing cleanup tags: {expected_tags - all_tags}"
>>>>>>> users/fde-platform-agent/fde-hiring-test-3/boyevche
