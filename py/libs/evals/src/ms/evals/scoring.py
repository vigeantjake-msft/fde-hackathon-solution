# Copyright (c) Microsoft. All rights reserved.
"""Scoring functions for evaluation — mirrors the platform's deterministic scoring logic.

Implements the same scoring algorithm as docs/eval/run_eval.py so that
evaluation suites produce results comparable to the official harness.
"""

from collections.abc import Sequence

from ms.evals.models import DimensionScores
from ms.evals.models import EvalCase
from ms.evals.models import EvalResult
from ms.evals.models import EvalSuite
from ms.evals.models import TicketScore

# ── Dimension weights (match the platform exactly) ──────────────────

WEIGHT_CATEGORY = 0.20
WEIGHT_PRIORITY = 0.20
WEIGHT_ROUTING = 0.20
WEIGHT_MISSING_INFO = 0.15
WEIGHT_ESCALATION = 0.10

CLASSIFICATION_WEIGHT_SUM = (
    WEIGHT_CATEGORY + WEIGHT_PRIORITY + WEIGHT_ROUTING + WEIGHT_MISSING_INFO + WEIGHT_ESCALATION
)

WEIGHTS: dict[str, float] = {
    "category": WEIGHT_CATEGORY,
    "priority": WEIGHT_PRIORITY,
    "routing": WEIGHT_ROUTING,
    "missing_info": WEIGHT_MISSING_INFO,
    "escalation": WEIGHT_ESCALATION,
}

# ── Closed label sets ────────────────────────────────────────────────

CATEGORIES: tuple[str, ...] = (
    "Access & Authentication",
    "Hardware & Peripherals",
    "Network & Connectivity",
    "Software & Applications",
    "Security & Compliance",
    "Data & Storage",
    "General Inquiry",
    "Not a Support Ticket",
)

TEAMS: tuple[str, ...] = (
    "Identity & Access Management",
    "Endpoint Engineering",
    "Network Operations",
    "Enterprise Applications",
    "Security Operations",
    "Data Platform",
    "None",
)


# ── Helpers ──────────────────────────────────────────────────────────


def _normalize(text: str) -> str:
    """Lowercase and strip for case-insensitive comparison."""
    return text.strip().lower()


def coerce_bool(value: object) -> bool:
    """Safely coerce a value to boolean.

    Handles string representations like "true"/"false" that participants
    may return from their API.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes"}
    if isinstance(value, int):
        return value != 0
    return False


# ── Submission-level aggregate metrics ───────────────────────────────


def macro_f1(
    candidates: Sequence[str],
    golds: Sequence[str],
    label_set: Sequence[str],
) -> float:
    """Macro-averaged F1 over a closed set of class labels.

    Computes per-class F1 then averages across classes that appear in
    either golds or candidates. Classes absent from both are excluded.
    """
    candidate_norm = [_normalize(c) for c in candidates]
    gold_norm = [_normalize(g) for g in golds]
    label_norm = [_normalize(label) for label in label_set]

    f1_scores: list[float] = []
    for label in label_norm:
        tp = sum(1 for c, g in zip(candidate_norm, gold_norm, strict=False) if c == label and g == label)
        fp = sum(1 for c, g in zip(candidate_norm, gold_norm, strict=False) if c == label and g != label)
        fn = sum(1 for c, g in zip(candidate_norm, gold_norm, strict=False) if c != label and g == label)

        if tp + fp + fn == 0:
            continue

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        f1_scores.append(f1)

    return sum(f1_scores) / len(f1_scores) if f1_scores else 0.0


def binary_f1(candidates: Sequence[bool], golds: Sequence[bool]) -> float:
    """F1 for the positive class (True) in binary classification.

    Returns 1.0 when there are no positive cases in either gold or predictions.
    """
    tp = sum(1 for c, g in zip(candidates, golds, strict=False) if c and g)
    fp = sum(1 for c, g in zip(candidates, golds, strict=False) if c and not g)
    fn = sum(1 for c, g in zip(candidates, golds, strict=False) if not c and g)

    if tp + fp + fn == 0:
        return 1.0

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0

    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


# ── Per-ticket scoring ───────────────────────────────────────────────


def score_category(pred: str | None, gold: str) -> float:
    """Exact match, case-insensitive. Returns 0.0 or 1.0."""
    if not pred:
        return 0.0
    return 1.0 if _normalize(pred) == _normalize(gold) else 0.0


def score_priority(pred: str | None, gold: str) -> float:
    """Priority match with partial credit for off-by-one.

    Same level     -> 1.0
    Off by 1 level -> 0.67
    Off by 2+      -> 0.0
    """
    order = {"P1": 0, "P2": 1, "P3": 2, "P4": 3}
    p = order.get(pred.strip().upper() if pred else "", -1)
    g = order.get(gold.strip().upper(), -1)
    if p == -1 or g == -1:
        return 0.0
    distance = abs(p - g)
    if distance == 0:
        return 1.0
    if distance == 1:
        return 0.67
    return 0.0


def score_routing(pred: str | None, gold: str) -> float:
    """Exact match, case-insensitive. Returns 0.0 or 1.0."""
    if not pred:
        return 0.0
    return 1.0 if _normalize(pred) == _normalize(gold) else 0.0


def score_escalation(pred: bool | None, gold: bool) -> float:
    """Binary match. Returns 0.0 or 1.0."""
    if pred is None:
        return 0.0
    return 1.0 if bool(pred) == bool(gold) else 0.0


def score_missing_info(pred_list: list[str] | None, gold_list: list[str]) -> float:
    """Set F1 over the constrained missing-information vocabulary.

    Both empty -> 1.0 (correctly identified nothing is missing).
    """
    pred_set = {_normalize(s) for s in (pred_list or [])}
    gold_set = {_normalize(s) for s in gold_list}

    if not gold_set and not pred_set:
        return 1.0
    if not gold_set or not pred_set:
        return 0.0

    true_positives = len(pred_set & gold_set)
    precision = true_positives / len(pred_set)
    recall = true_positives / len(gold_set)

    if precision + recall == 0:
        return 0.0
    return 2.0 * precision * recall / (precision + recall)


# ── Score a single ticket ────────────────────────────────────────────


def score_ticket(pred: dict[str, object], gold: dict[str, object]) -> TicketScore:
    """Score a single prediction against gold, returning a structured result."""
    cat = score_category(_str_or_none(pred.get("category")), str(gold["category"]))
    pri = score_priority(_str_or_none(pred.get("priority")), str(gold["priority"]))
    rte = score_routing(_str_or_none(pred.get("assigned_team")), str(gold["assigned_team"]))

    pred_missing = pred.get("missing_information")
    miss = score_missing_info(
        pred_missing if isinstance(pred_missing, list) else [],
        list(gold.get("missing_information", [])),  # type: ignore[arg-type]
    )

    pred_esc = pred.get("needs_escalation")
    esc = score_escalation(
        coerce_bool(pred_esc) if pred_esc is not None else None,
        bool(gold["needs_escalation"]),
    )

    weighted_total = (
        WEIGHT_CATEGORY * cat
        + WEIGHT_PRIORITY * pri
        + WEIGHT_ROUTING * rte
        + WEIGHT_MISSING_INFO * miss
        + WEIGHT_ESCALATION * esc
    )

    return TicketScore(
        ticket_id=str(pred.get("ticket_id", gold.get("ticket_id", ""))),
        category=cat,
        priority=pri,
        routing=rte,
        missing_info=miss,
        escalation=esc,
        weighted_total=weighted_total,
    )


def _str_or_none(val: object) -> str | None:
    """Convert a value to str or None."""
    if val is None:
        return None
    return str(val)


# ── Score a full evaluation suite ────────────────────────────────────


def score_eval_suite(
    suite: EvalSuite,
    candidate_responses: list[dict[str, object]],
    cases: list[EvalCase],
) -> EvalResult:
    """Score candidate responses against an evaluation suite.

    Uses the same submission-level metrics as the platform:
      - category:     macro F1 across 8 categories
      - priority:     mean ordinal partial credit
      - routing:      macro F1 across 7 teams
      - missing_info: mean per-ticket set F1
      - escalation:   binary F1 on the positive class
    """
    gold_answers = [case.gold for case in cases]
    cand_by_id = {str(c.get("ticket_id", "")): c for c in candidate_responses}

    per_ticket: list[TicketScore] = []
    all_cat_cands: list[str] = []
    all_cat_golds: list[str] = []
    all_rte_cands: list[str] = []
    all_rte_golds: list[str] = []
    all_esc_cands: list[bool] = []
    all_esc_golds: list[bool] = []
    all_pri_scores: list[float] = []
    all_miss_scores: list[float] = []
    errors: list[str] = []

    for gold in gold_answers:
        tid = gold.ticket_id
        cand = cand_by_id.get(tid)

        if cand is None:
            errors.append(f"Missing response for ticket {tid}")
            per_ticket.append(
                TicketScore(
                    ticket_id=tid,
                    category=0.0,
                    priority=0.0,
                    routing=0.0,
                    missing_info=0.0,
                    escalation=0.0,
                    weighted_total=0.0,
                )
            )
            all_cat_cands.append("")
            all_cat_golds.append(_normalize(gold.category))
            all_rte_cands.append("")
            all_rte_golds.append(_normalize(gold.assigned_team))
            all_esc_cands.append(False)
            all_esc_golds.append(gold.needs_escalation)
            all_pri_scores.append(0.0)
            all_miss_scores.append(0.0)
        else:
            gold_dict: dict[str, object] = {
                "ticket_id": gold.ticket_id,
                "category": gold.category,
                "priority": gold.priority,
                "assigned_team": gold.assigned_team,
                "needs_escalation": gold.needs_escalation,
                "missing_information": gold.missing_information,
            }
            ticket_result = score_ticket(cand, gold_dict)
            per_ticket.append(ticket_result)

            all_cat_cands.append(_normalize(str(cand.get("category", ""))))
            all_cat_golds.append(_normalize(gold.category))
            all_rte_cands.append(_normalize(str(cand.get("assigned_team", ""))))
            all_rte_golds.append(_normalize(gold.assigned_team))
            all_esc_cands.append(coerce_bool(cand.get("needs_escalation")))
            all_esc_golds.append(gold.needs_escalation)
            all_pri_scores.append(ticket_result.priority)
            all_miss_scores.append(ticket_result.missing_info)

    n = len(per_ticket)

    category_score = macro_f1(all_cat_cands, all_cat_golds, CATEGORIES)
    priority_score = sum(all_pri_scores) / n if n > 0 else 0.0
    routing_score = macro_f1(all_rte_cands, all_rte_golds, TEAMS)
    missing_info_score = sum(all_miss_scores) / n if n > 0 else 0.0
    escalation_score = binary_f1(all_esc_cands, all_esc_golds)

    weighted_total = (
        WEIGHT_CATEGORY * category_score
        + WEIGHT_PRIORITY * priority_score
        + WEIGHT_ROUTING * routing_score
        + WEIGHT_MISSING_INFO * missing_info_score
        + WEIGHT_ESCALATION * escalation_score
    )

    classification_score = round(weighted_total / CLASSIFICATION_WEIGHT_SUM * 85, 1)

    return EvalResult(
        suite=suite,
        classification_score=classification_score,
        dimension_scores=DimensionScores(
            category=round(category_score, 4),
            priority=round(priority_score, 4),
            routing=round(routing_score, 4),
            missing_info=round(missing_info_score, 4),
            escalation=round(escalation_score, 4),
        ),
        tickets_scored=n - len(errors),
        tickets_errored=len(errors),
        per_ticket=per_ticket,
        errors=errors,
    )
