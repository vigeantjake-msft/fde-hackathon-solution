# Copyright (c) Microsoft. All rights reserved.
"""Scenario metadata and composite eval scenario models."""

from enum import StrEnum

from ms.common.models.base import FrozenBaseModel

from ms.evals.models.ticket import Ticket
from ms.evals.models.triage_decision import TriageDecision


class ScenarioCategory(StrEnum):
    """High-level category of an evaluation scenario."""

    DATA_CLEANUP = "data_cleanup"
    RESPONSIBLE_AI = "responsible_ai"


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
