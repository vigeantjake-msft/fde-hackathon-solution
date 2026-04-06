# Copyright (c) Microsoft. All rights reserved.
"""Tests for the Pydantic models used in evaluation scenarios."""

import pytest
from pydantic import ValidationError  # noqa: TID251

from ms.evals.models import AssignedTeam
from ms.evals.models import Category
from ms.evals.models import Channel
from ms.evals.models import EvalScenario
from ms.evals.models import MissingInformation
from ms.evals.models import Priority
from ms.evals.models import Reporter
from ms.evals.models import ScenarioTag
from ms.evals.models import TicketInput
from ms.evals.models import TriageGold


class TestReporter:
    def test_valid_reporter(self):
        reporter = Reporter(name="Jane Doe", email="jane@contoso.com", department="IT")
        assert reporter.name == "Jane Doe"
        assert reporter.email == "jane@contoso.com"
        assert reporter.department == "IT"

    def test_reporter_is_frozen(self):
        reporter = Reporter(name="Jane", email="jane@contoso.com", department="IT")
        with pytest.raises(ValidationError):
            reporter.name = "John"


class TestTicketInput:
    def test_valid_ticket(self):
        ticket = TicketInput(
            ticket_id="INC-0001",
            subject="Test",
            description="Test description",
            reporter=Reporter(name="Jane", email="jane@contoso.com", department="IT"),
            created_at="2026-03-17T09:00:00Z",
            channel=Channel.EMAIL,
        )
        assert ticket.ticket_id == "INC-0001"
        assert ticket.attachments == []

    def test_ticket_with_attachments(self):
        ticket = TicketInput(
            ticket_id="INC-0002",
            subject="Test",
            description="Test",
            reporter=Reporter(name="Jane", email="jane@contoso.com", department="IT"),
            created_at="2026-03-17T09:00:00Z",
            channel=Channel.PORTAL,
            attachments=["file1.png", "file2.pdf"],
        )
        assert len(ticket.attachments) == 2


class TestTriageGold:
    def test_valid_gold(self):
        gold = TriageGold(
            ticket_id="INC-0001",
            category=Category.NETWORK,
            priority=Priority.P3,
            assigned_team=AssignedTeam.NETWORK_OPS,
            needs_escalation=False,
            missing_information=[],
            next_best_action="Investigate the issue.",
            remediation_steps=["Step 1", "Step 2"],
        )
        assert gold.category == Category.NETWORK
        assert gold.priority == Priority.P3

    def test_gold_with_missing_info(self):
        gold = TriageGold(
            ticket_id="INC-0001",
            category=Category.HARDWARE,
            priority=Priority.P2,
            assigned_team=AssignedTeam.ENDPOINT,
            needs_escalation=True,
            missing_information=[MissingInformation.DEVICE_INFO, MissingInformation.ERROR_MESSAGE],
            next_best_action="Check device.",
            remediation_steps=["Step 1"],
        )
        assert len(gold.missing_information) == 2


class TestEvalScenario:
    def _make_scenario(self) -> EvalScenario:
        return EvalScenario(
            ticket=TicketInput(
                ticket_id="EVAL-TEST-0001",
                subject="Test",
                description="Test description",
                reporter=Reporter(name="Jane", email="jane@contoso.com", department="IT"),
                created_at="2026-03-17T09:00:00Z",
                channel=Channel.EMAIL,
            ),
            gold=TriageGold(
                ticket_id="EVAL-TEST-0001",
                category=Category.GENERAL,
                priority=Priority.P4,
                assigned_team=AssignedTeam.NONE,
                needs_escalation=False,
                missing_information=[],
                next_best_action="No action needed.",
                remediation_steps=[],
            ),
            tags=[ScenarioTag.EMPTY_DESCRIPTION],
            description="Test scenario",
            category="data_cleanup",
        )

    def test_to_input_dict(self):
        scenario = self._make_scenario()
        input_dict = scenario.to_input_dict()
        assert input_dict["ticket_id"] == "EVAL-TEST-0001"
        assert input_dict["channel"] == "email"
        assert isinstance(input_dict, dict)

    def test_to_gold_dict(self):
        scenario = self._make_scenario()
        gold_dict = scenario.to_gold_dict()
        assert gold_dict["ticket_id"] == "EVAL-TEST-0001"
        assert gold_dict["category"] == "General Inquiry"
        assert gold_dict["priority"] == "P4"
        assert isinstance(gold_dict, dict)

    def test_input_and_gold_ticket_ids_match(self):
        scenario = self._make_scenario()
        assert scenario.ticket.ticket_id == scenario.gold.ticket_id


class TestEnumValues:
    """Verify enum values match the challenge schema exactly."""

    def test_categories_count(self):
        assert len(Category) == 8

    def test_priorities_count(self):
        assert len(Priority) == 4

    def test_teams_count(self):
        assert len(AssignedTeam) == 7

    def test_missing_info_count(self):
        assert len(MissingInformation) == 16

    def test_channels_count(self):
        assert len(Channel) == 4

    def test_category_values_match_schema(self):
        expected = {
            "Access & Authentication",
            "Hardware & Peripherals",
            "Network & Connectivity",
            "Software & Applications",
            "Security & Compliance",
            "Data & Storage",
            "General Inquiry",
            "Not a Support Ticket",
        }
        actual = {c.value for c in Category}
        assert actual == expected

    def test_priority_values_match_schema(self):
        expected = {"P1", "P2", "P3", "P4"}
        actual = {p.value for p in Priority}
        assert actual == expected

    def test_team_values_match_schema(self):
        expected = {
            "Identity & Access Management",
            "Endpoint Engineering",
            "Network Operations",
            "Enterprise Applications",
            "Security Operations",
            "Data Platform",
            "None",
        }
        actual = {t.value for t in AssignedTeam}
        assert actual == expected

    def test_missing_info_values_match_schema(self):
        expected = {
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
        actual = {m.value for m in MissingInformation}
        assert actual == expected
