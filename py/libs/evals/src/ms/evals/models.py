# Copyright (c) Microsoft. All rights reserved.
"""Pydantic models for evaluation test cases and results."""

from enum import Enum

from ms.common.models.base import FrozenBaseModel


class EvalSuite(str, Enum):
    """Evaluation suite identifier."""

    DATA_CLEANUP = "data_cleanup"
    RESPONSIBLE_AI = "responsible_ai"


class EvalTicketReporter(FrozenBaseModel):
    """Reporter details for a synthetic evaluation ticket."""

    name: str
    email: str
    department: str


class EvalTicket(FrozenBaseModel):
    """A synthetic ticket used in evaluation test cases."""

    ticket_id: str
    subject: str
    description: str
    reporter: EvalTicketReporter
    created_at: str
    channel: str
    attachments: list[str] = []


class EvalGoldAnswer(FrozenBaseModel):
    """Expected gold-standard triage output for an evaluation ticket."""

    ticket_id: str
    category: str
    priority: str
    assigned_team: str
    needs_escalation: bool
    missing_information: list[str]


class EvalCase(FrozenBaseModel):
    """A single evaluation test case: ticket + expected answer + metadata."""

    suite: EvalSuite
    case_id: str
    description: str
    ticket: EvalTicket
    gold: EvalGoldAnswer


class TicketScore(FrozenBaseModel):
    """Per-ticket scoring breakdown."""

    ticket_id: str
    category: float
    priority: float
    routing: float
    missing_info: float
    escalation: float
    weighted_total: float


class DimensionScores(FrozenBaseModel):
    """Submission-level dimension scores (0.0 – 1.0 each)."""

    category: float
    priority: float
    routing: float
    missing_info: float
    escalation: float


class EvalResult(FrozenBaseModel):
    """Full evaluation result for one suite."""

    suite: EvalSuite
    classification_score: float
    dimension_scores: DimensionScores
    tickets_scored: int
    tickets_errored: int
    per_ticket: list[TicketScore]
    errors: list[str]
