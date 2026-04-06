# Copyright (c) Microsoft. All rights reserved.
"""Tests for data cleanup evaluation scenarios.

Validates that all data cleanup scenarios are well-formed, have matching
ticket IDs between input and gold, use valid enum values, and that the
edge-case properties (long text, base64, HTML, etc.) are actually present
in the test data.
"""

import json

from ms.evals.models import ScenarioTag
from ms.evals.scenarios.data_cleanup import get_all_data_cleanup_scenarios
from ms.evals.scenarios.data_cleanup import scenario_attachment_reference_only
from ms.evals.scenarios.data_cleanup import scenario_base64_image_in_description
from ms.evals.scenarios.data_cleanup import scenario_empty_description
from ms.evals.scenarios.data_cleanup import scenario_excessive_whitespace_and_formatting
from ms.evals.scenarios.data_cleanup import scenario_extremely_long_single_paragraph
from ms.evals.scenarios.data_cleanup import scenario_garbled_encoding
from ms.evals.scenarios.data_cleanup import scenario_massive_email_signature
from ms.evals.scenarios.data_cleanup import scenario_mixed_language
from ms.evals.scenarios.data_cleanup import scenario_multiple_base64_blocks_with_headers
from ms.evals.scenarios.data_cleanup import scenario_raw_html_email
from ms.evals.scenarios.data_cleanup import scenario_repeated_content
from ms.evals.scenarios.data_cleanup import scenario_very_long_email_chain


class TestDataCleanupScenarioCount:
    def test_has_at_least_12_scenarios(self):
        scenarios = get_all_data_cleanup_scenarios()
        assert len(scenarios) >= 12

    def test_all_have_data_cleanup_category(self):
        for scenario in get_all_data_cleanup_scenarios():
            assert scenario.category == "data_cleanup"


class TestDataCleanupScenarioStructure:
    def test_ticket_ids_are_unique(self):
        scenarios = get_all_data_cleanup_scenarios()
        ids = [s.ticket.ticket_id for s in scenarios]
        assert len(ids) == len(set(ids))

    def test_ticket_id_matches_gold(self):
        for scenario in get_all_data_cleanup_scenarios():
            assert scenario.ticket.ticket_id == scenario.gold.ticket_id

    def test_all_have_tags(self):
        for scenario in get_all_data_cleanup_scenarios():
            assert len(scenario.tags) > 0

    def test_all_have_description(self):
        for scenario in get_all_data_cleanup_scenarios():
            assert len(scenario.description) > 10

    def test_gold_has_remediation_steps(self):
        for scenario in get_all_data_cleanup_scenarios():
            assert len(scenario.gold.remediation_steps) > 0

    def test_gold_has_next_best_action(self):
        for scenario in get_all_data_cleanup_scenarios():
            assert len(scenario.gold.next_best_action) > 10

    def test_to_input_dict_is_valid_json_serializable(self):
        for scenario in get_all_data_cleanup_scenarios():
            input_dict = scenario.to_input_dict()
            json_str = json.dumps(input_dict)
            assert len(json_str) > 0

    def test_to_gold_dict_is_valid_json_serializable(self):
        for scenario in get_all_data_cleanup_scenarios():
            gold_dict = scenario.to_gold_dict()
            json_str = json.dumps(gold_dict)
            assert len(json_str) > 0


class TestVeryLongEmailChain:
    def test_description_is_very_long(self):
        scenario = scenario_very_long_email_chain()
        assert len(scenario.ticket.description) > 3000

    def test_has_email_chain_tag(self):
        scenario = scenario_very_long_email_chain()
        assert ScenarioTag.EMAIL_CHAIN in scenario.tags

    def test_contains_nested_reply_markers(self):
        scenario = scenario_very_long_email_chain()
        assert ">" in scenario.ticket.description
        assert "Original message from" in scenario.ticket.description

    def test_real_issue_present_in_description(self):
        scenario = scenario_very_long_email_chain()
        assert "VPN" in scenario.ticket.description


class TestBase64ImageInDescription:
    def test_contains_base64_data(self):
        scenario = scenario_base64_image_in_description()
        assert "base64," in scenario.ticket.description

    def test_description_is_longer_than_normal(self):
        scenario = scenario_base64_image_in_description()
        assert len(scenario.ticket.description) > 5000

    def test_has_base64_tag(self):
        scenario = scenario_base64_image_in_description()
        assert ScenarioTag.BASE64_CONTENT in scenario.tags

    def test_real_issue_present(self):
        scenario = scenario_base64_image_in_description()
        assert "flickering" in scenario.ticket.description.lower()


class TestRawHtmlEmail:
    def test_contains_html_tags(self):
        scenario = scenario_raw_html_email()
        assert "<html>" in scenario.ticket.description.lower()
        assert "<style>" in scenario.ticket.description.lower()

    def test_has_html_email_tag(self):
        scenario = scenario_raw_html_email()
        assert ScenarioTag.HTML_EMAIL in scenario.tags

    def test_real_issue_present(self):
        scenario = scenario_raw_html_email()
        assert "SAP" in scenario.ticket.description


class TestMassiveEmailSignature:
    def test_signature_longer_than_issue(self):
        scenario = scenario_massive_email_signature()
        desc = scenario.ticket.description
        issue_end = desc.index("━")
        issue_text = desc[:issue_end].strip()
        signature_text = desc[issue_end:]
        assert len(signature_text) > len(issue_text) * 10

    def test_has_signature_tag(self):
        scenario = scenario_massive_email_signature()
        assert ScenarioTag.MASSIVE_SIGNATURE in scenario.tags


class TestGarbledEncoding:
    def test_contains_mojibake(self):
        scenario = scenario_garbled_encoding()
        desc = scenario.ticket.description
        # Check for UTF-8 misinterpreted as latin-1 artifacts
        assert "â" in desc

    def test_has_garbled_text_tag(self):
        scenario = scenario_garbled_encoding()
        assert ScenarioTag.GARBLED_TEXT in scenario.tags

    def test_real_issue_extractable(self):
        scenario = scenario_garbled_encoding()
        assert "Wi-Fi" in scenario.ticket.description


class TestEmptyDescription:
    def test_description_is_effectively_empty(self):
        scenario = scenario_empty_description()
        assert scenario.ticket.description.strip() == ""

    def test_has_empty_description_tag(self):
        scenario = scenario_empty_description()
        assert ScenarioTag.EMPTY_DESCRIPTION in scenario.tags

    def test_gold_requests_missing_information(self):
        scenario = scenario_empty_description()
        assert len(scenario.gold.missing_information) >= 3


class TestRepeatedContent:
    def test_description_has_repeated_blocks(self):
        scenario = scenario_repeated_content()
        desc = scenario.ticket.description
        # Count occurrences of the key phrase
        assert desc.count("Outlook keeps crashing") >= 10

    def test_has_repeated_content_tag(self):
        scenario = scenario_repeated_content()
        assert ScenarioTag.REPEATED_CONTENT in scenario.tags


class TestMixedLanguage:
    def test_contains_non_latin_characters(self):
        scenario = scenario_mixed_language()
        desc = scenario.ticket.description
        # Check for CJK characters
        assert any("\u4e00" <= ch <= "\u9fff" for ch in desc)

    def test_contains_english(self):
        scenario = scenario_mixed_language()
        assert "VPN" in scenario.ticket.description

    def test_has_mixed_language_tag(self):
        scenario = scenario_mixed_language()
        assert ScenarioTag.MIXED_LANGUAGE in scenario.tags


class TestAttachmentReferenceOnly:
    def test_description_references_attachments(self):
        scenario = scenario_attachment_reference_only()
        assert "attached" in scenario.ticket.description.lower()

    def test_description_is_very_short(self):
        scenario = scenario_attachment_reference_only()
        assert len(scenario.ticket.description) < 50

    def test_has_actual_attachments(self):
        scenario = scenario_attachment_reference_only()
        assert len(scenario.ticket.attachments) > 0

    def test_has_attachment_only_tag(self):
        scenario = scenario_attachment_reference_only()
        assert ScenarioTag.ATTACHMENT_ONLY in scenario.tags

    def test_gold_requires_more_info(self):
        scenario = scenario_attachment_reference_only()
        assert len(scenario.gold.missing_information) >= 3


class TestExcessiveWhitespace:
    def test_description_has_excessive_whitespace(self):
        scenario = scenario_excessive_whitespace_and_formatting()
        desc = scenario.ticket.description
        blank_line_count = desc.count("\n\n")
        assert blank_line_count > 5

    def test_has_whitespace_tag(self):
        scenario = scenario_excessive_whitespace_and_formatting()
        assert ScenarioTag.EXCESSIVE_WHITESPACE in scenario.tags


class TestMultipleBase64Blocks:
    def test_contains_multiple_mime_boundaries(self):
        scenario = scenario_multiple_base64_blocks_with_headers()
        desc = scenario.ticket.description
        assert desc.count("------=_Part_") >= 2

    def test_contains_content_transfer_encoding(self):
        scenario = scenario_multiple_base64_blocks_with_headers()
        assert "Content-Transfer-Encoding: base64" in scenario.ticket.description

    def test_has_base64_tag(self):
        scenario = scenario_multiple_base64_blocks_with_headers()
        assert ScenarioTag.BASE64_CONTENT in scenario.tags

    def test_real_issue_present(self):
        scenario = scenario_multiple_base64_blocks_with_headers()
        assert "DRIVER_IRQL_NOT_LESS_OR_EQUAL" in scenario.ticket.description


class TestExtremelyLongSingleParagraph:
    def test_description_is_long(self):
        scenario = scenario_extremely_long_single_paragraph()
        assert len(scenario.ticket.description) > 2000

    def test_has_long_email_tag(self):
        scenario = scenario_extremely_long_single_paragraph()
        assert ScenarioTag.LONG_EMAIL in scenario.tags

    def test_core_issue_present(self):
        scenario = scenario_extremely_long_single_paragraph()
        assert "SAP" in scenario.ticket.description
        assert "GL reconciliation" in scenario.ticket.description
