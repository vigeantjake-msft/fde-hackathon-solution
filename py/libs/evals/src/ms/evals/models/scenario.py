# Copyright (c) Microsoft. All rights reserved.
<<<<<<< HEAD
"""Scenario metadata and composite eval scenario models."""
=======
"""Pydantic models for evaluation scenarios."""
>>>>>>> users/fde-platform-agent/fde-hiring-test-3/boyevche

from enum import StrEnum

from ms.common.models.base import FrozenBaseModel

<<<<<<< HEAD
from ms.evals.models.ticket import Ticket
from ms.evals.models.triage_decision import TriageDecision


class ScenarioCategory(StrEnum):
    """High-level category of an evaluation scenario."""
=======

class ScenarioCategory(StrEnum):
    """Top-level category for evaluation scenarios."""
>>>>>>> users/fde-platform-agent/fde-hiring-test-3/boyevche

    DATA_CLEANUP = "data_cleanup"
    RESPONSIBLE_AI = "responsible_ai"


<<<<<<< HEAD
class ScenarioMetadata(FrozenBaseModel):
    """Metadata describing what an evaluation scenario tests.

    Provides context about the scenario's purpose, the specific challenge
    it poses, and its expected difficulty for the triage system.
    """

    scenario_id: str
    category: ScenarioCategory
    subcategory: str
    description: str
    challenge: str


class EvalScenario(FrozenBaseModel):
    """A complete evaluation scenario: ticket + expected triage + metadata.

    This is the primary unit of evaluation. Each scenario pairs an input
    ticket with its expected triage decision and metadata about what the
    scenario is testing.
    """

    metadata: ScenarioMetadata
    ticket: Ticket
    expected: TriageDecision
=======
class EvalReporter(FrozenBaseModel):
    """Reporter details for an evaluation ticket."""

    name: str
    email: str
    department: str


class EvalTicket(FrozenBaseModel):
    """A synthetic ticket used as input for an evaluation scenario."""

    ticket_id: str
    subject: str
    description: str
    reporter: EvalReporter
    created_at: str
    channel: str
    attachments: list[str] = []


class ExpectedTriage(FrozenBaseModel):
    """Expected triage output fields.

    Fields set to None indicate "any valid value is acceptable".
    """

    category: str | None = None
    priority: str | None = None
    assigned_team: str | None = None
    needs_escalation: bool | None = None
    missing_information: list[str] | None = None


class ResponseConstraint(FrozenBaseModel):
    """Constraints on what a valid response must satisfy.

    Used for responsible AI checks: ensuring the response doesn't
    contain forbidden strings, follow injected instructions, etc.
    """

    must_be_valid_json: bool = True
    must_have_valid_category: bool = True
    must_have_valid_priority: bool = True
    must_have_valid_team: bool = True
    must_not_contain: list[str] = []
    must_not_contain_in_remediation: list[str] = []


class EvalScenario(FrozenBaseModel):
    """A single evaluation scenario with ticket input, expectations, and constraints."""

    scenario_id: str
    name: str
    description: str
    category: ScenarioCategory
    tags: list[str] = []
    ticket: EvalTicket
    expected_triage: ExpectedTriage | None = None
    constraints: ResponseConstraint = ResponseConstraint()
>>>>>>> users/fde-platform-agent/fde-hiring-test-3/boyevche
