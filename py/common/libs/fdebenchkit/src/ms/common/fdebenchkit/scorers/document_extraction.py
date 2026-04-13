# Copyright (c) Microsoft. All rights reserved.
"""Deterministic scoring for Task 2: Document Data Extraction.

Scores 8 extraction dimensions against gold answers from FDA DailyMed
drug labels. Each dimension uses either exact match (after normalization)
or set F1 — no LLM involved.

Dimensions and weights:
    1. drug_name          — 15% — exact match after normalization (binary)
    2. indications        — 15% — token overlap on condition, exact match on population
    3. dosage_forms       — 15% — set F1 on form + strengths + route (closed set)
    4. warnings           —  5% — set F1 on warning categories (closed set)
    5. contraindications  — 15% — soft set F1 using token overlap
    6. adverse_reactions  — 20% — token overlap on reaction, exact match on frequency
    7. active_ingredients — 10% — token overlap on name, exact match on strength + unit
    8. metadata           —  5% — token F1 on manufacturer + storage


Scoring philosophy:
  - Closed-set fields (form, route, category, severity, frequency, unit,
    strength) use exact match after normalization — fair and unambiguous.
  - Free-text extraction fields (condition, contraindication strings,
    reaction names, ingredient names) use token-level F1 so that minor
    wording differences ("type 2 diabetes" vs "type 2 diabetes mellitus")
    receive proportional credit instead of a binary 0.
  - Empty gold fields are excluded from the document score (not rewarded).
"""

import re
from collections.abc import Callable
from collections.abc import Sequence
from typing import Any

from ms.common.fdebenchkit.scorers._utils import best_token_f1
from ms.common.fdebenchkit.scorers._utils import normalize_text
from ms.common.fdebenchkit.scorers._utils import set_f1
from ms.common.fdebenchkit.scorers._utils import token_f1

# ── Weights (sum to 1.0) ─────────────────────────────────────────────

WEIGHT_DRUG_NAME = 0.15
WEIGHT_INDICATIONS = 0.15
WEIGHT_DOSAGE_FORMS = 0.15
WEIGHT_WARNINGS = 0.05
WEIGHT_CONTRAINDICATIONS = 0.15
WEIGHT_ADVERSE_REACTIONS = 0.20
WEIGHT_ACTIVE_INGREDIENTS = 0.10
WEIGHT_METADATA = 0.05

DIMENSION_WEIGHTS: dict[str, float] = {
    "drug_name": WEIGHT_DRUG_NAME,
    "indications": WEIGHT_INDICATIONS,
    "dosage_forms": WEIGHT_DOSAGE_FORMS,
    "warnings": WEIGHT_WARNINGS,
    "contraindications": WEIGHT_CONTRAINDICATIONS,
    "adverse_reactions": WEIGHT_ADVERSE_REACTIONS,
    "active_ingredients": WEIGHT_ACTIVE_INGREDIENTS,
    "metadata": WEIGHT_METADATA,
}


# ── Text normalization ────────────────────────────────────────────────


def _normalize_drug_name(name: str) -> str:
    """Normalize a drug name for comparison.

    Removes common suffixes (tablets, injection, etc.), trademark symbols,
    and normalizes casing/whitespace.
    """
    name = normalize_text(name)
    # Remove common dosage form suffixes
    name = re.sub(
        r"\s+(tablets?|capsules?|injection|solution|cream|ointment|gel|patch|suspension|oral)\s*$",
        "",
        name,
    )
    # Remove trademark/registered symbols
    name = re.sub(r"[®™©]", "", name)
    return name.strip()


# ── Set F1 ────────────────────────────────────────────────────────────


# ── Per-dimension scorers ─────────────────────────────────────────────
#
# Each scorer takes (candidate_value, gold_value) and returns 0.0–1.0.
# They are independent and can be tested/used individually.


def _soft_set_f1(
    candidate_items: Sequence[Any],
    gold_items: Sequence[Any],
    similarity_fn: Callable[[Any, Any], float],
) -> float:
    """Soft set F1 over structured items using a custom deterministic similarity."""
    if not gold_items and not candidate_items:
        return 1.0
    if not gold_items or not candidate_items:
        return 0.0

    recall_scores = [max(similarity_fn(candidate, gold) for candidate in candidate_items) for gold in gold_items]
    recall = sum(recall_scores) / len(recall_scores)

    precision_scores = [max(similarity_fn(candidate, gold) for gold in gold_items) for candidate in candidate_items]
    precision = sum(precision_scores) / len(precision_scores)

    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def score_drug_name(candidate: str, gold: str) -> float:
    """Binary exact match on drug name after normalization.

    Returns 1.0 for exact match, 0.0 otherwise. No partial credit —
    drug names are either correct or not.
    """
    c = _normalize_drug_name(candidate)
    g = _normalize_drug_name(gold)

    if not c or not g:
        return 0.0
    return 1.0 if c == g else 0.0


def score_indications(
    candidate: Sequence[dict[str, str]],
    gold: Sequence[dict[str, str]],
) -> float:
    """Soft set F1 on indications using token overlap on condition.

    Population is a closed set (adults/pediatric) matched exactly.
    Condition is free text — uses token F1 for robust matching so that
    "type 2 diabetes" vs "type 2 diabetes mellitus" scores ~0.86.
    """
    c_items = [
        (
            normalize_text(ind.get("condition", "")),
            normalize_text(ind.get("population", "adults")),
        )
        for ind in candidate
        if ind.get("condition")
    ]
    g_items = [
        (
            normalize_text(ind.get("condition", "")),
            normalize_text(ind.get("population", "adults")),
        )
        for ind in gold
        if ind.get("condition")
    ]

    def _similarity(candidate_item: tuple[str, str], gold_item: tuple[str, str]) -> float:
        candidate_condition, candidate_population = candidate_item
        gold_condition, gold_population = gold_item
        if candidate_population != gold_population:
            return 0.0
        return token_f1(candidate_condition, gold_condition)

    return _soft_set_f1(c_items, g_items, _similarity)


def score_dosage_forms(
    candidate: Sequence[dict[str, Any]],
    gold: Sequence[dict[str, Any]],
) -> float:
    """Set F1 on dosage forms, keyed on (form, route).

    Strengths are compared as a set within each matching (form, route) pair.
    """

    def _key(d: dict[str, Any]) -> str:
        form = normalize_text(str(d.get("form", "")))
        route = normalize_text(str(d.get("route", "")))
        strengths = sorted(normalize_text(s) for s in d.get("strengths", []))
        return f"{form}|{route}|{','.join(strengths)}"

    c_set = {_key(d) for d in candidate if d.get("form")}
    g_set = {_key(d) for d in gold if d.get("form")}
    return set_f1(c_set, g_set)


def score_warnings(
    candidate: Sequence[dict[str, str]],
    gold: Sequence[dict[str, str]],
) -> float:
    """Set F1 on warnings, keyed on (category, severity).

    The description field is not used for matching — it's free text and
    too noisy for deterministic comparison.
    """
    c_set = {
        f"{normalize_text(w.get('category', ''))}|{normalize_text(w.get('severity', ''))}"
        for w in candidate
        if w.get("category")
    }
    g_set = {
        f"{normalize_text(w.get('category', ''))}|{normalize_text(w.get('severity', ''))}"
        for w in gold
        if w.get("category")
    }
    return set_f1(c_set, g_set)


def score_contraindications(
    candidate: Sequence[str],
    gold: Sequence[str],
) -> float:
    """Soft set F1 on contraindication strings using token overlap.

    Contraindication gold entries are free-text phrases (avg 60 chars).
    Token F1 ensures minor wording differences receive proportional
    credit instead of binary 0.
    """
    c_set = {normalize_text(c) for c in candidate if c}
    g_set = {normalize_text(g) for g in gold if g}
    return best_token_f1(c_set, g_set)


def score_adverse_reactions(
    candidate: Sequence[dict[str, Any]],
    gold: Sequence[dict[str, Any]],
) -> float:
    """Soft set F1 on adverse reactions using token overlap on reaction name.

    Frequency is a closed set (common/uncommon/rare/very_common/very_rare)
    matched exactly. Reaction name is free text — uses token F1.
    ``incidence_percent`` is not used for matching.
    """
    c_items = [
        (
            normalize_text(r.get("reaction", "")),
            normalize_text(str(r.get("frequency", ""))),
        )
        for r in candidate
        if r.get("reaction")
    ]
    g_items = [
        (
            normalize_text(r.get("reaction", "")),
            normalize_text(str(r.get("frequency", ""))),
        )
        for r in gold
        if r.get("reaction")
    ]

    def _similarity(candidate_item: tuple[str, str], gold_item: tuple[str, str]) -> float:
        candidate_reaction, candidate_frequency = candidate_item
        gold_reaction, gold_frequency = gold_item
        if candidate_frequency != gold_frequency:
            return 0.0
        return token_f1(candidate_reaction, gold_reaction)

    return _soft_set_f1(c_items, g_items, _similarity)


def score_active_ingredients(
    candidate: Sequence[dict[str, str]],
    gold: Sequence[dict[str, str]],
) -> float:
    """Soft set F1 on active ingredients using token overlap on name.

    Strength and unit are closed-set values included in the match key.
    Name is free text (chemical names) — uses token F1 so that
    "metformin hcl" vs "metformin hydrochloride" gets partial credit.
    """

    def _item(ing: dict[str, str]) -> tuple[str, str, str]:
        return (
            normalize_text(ing.get("name", "")),
            normalize_text(str(ing.get("strength", ""))),
            normalize_text(str(ing.get("unit", ""))),
        )

    c_items = [_item(ingredient) for ingredient in candidate if ingredient.get("name")]
    g_items = [_item(ingredient) for ingredient in gold if ingredient.get("name")]

    def _similarity(candidate_item: tuple[str, str, str], gold_item: tuple[str, str, str]) -> float:
        candidate_name, candidate_strength, candidate_unit = candidate_item
        gold_name, gold_strength, gold_unit = gold_item
        if candidate_strength != gold_strength or candidate_unit != gold_unit:
            return 0.0
        return token_f1(candidate_name, gold_name)

    return _soft_set_f1(c_items, g_items, _similarity)


def score_metadata(candidate: dict[str, Any], gold: dict[str, Any]) -> float:
    """Token F1 on manufacturer and storage fields.

    Returns the average token F1 across populated gold metadata fields.
    Uses token-level matching instead of substring to handle minor
    formatting differences (e.g., "Pfizer Inc." vs "Pfizer, Inc").
    Returns 0.0 when gold has no metadata (excluded, not rewarded).
    """
    scores: list[float] = []

    # Manufacturer
    g_mfr = normalize_text(str(gold.get("manufacturer", "")))
    c_mfr = normalize_text(str(candidate.get("manufacturer", "")))
    if g_mfr:
        scores.append(token_f1(c_mfr, g_mfr))

    # Storage
    g_storage = normalize_text(str(gold.get("storage", "") or ""))
    c_storage = normalize_text(str(candidate.get("storage", "") or ""))
    if g_storage:
        scores.append(token_f1(c_storage, g_storage))

    if not scores:
        return 0.0  # no gold metadata to compare → excluded, not rewarded
    return sum(scores) / len(scores)


# ── Gold data presence check ──────────────────────────────────────────

# Maps dimension names to the gold field(s) that must be non-empty for
# that dimension to contribute to the weighted total.
_GOLD_FIELD_MAP: dict[str, list[str]] = {
    "drug_name": ["drug_name"],
    "indications": ["indications"],
    "dosage_forms": ["dosage_forms"],
    "warnings": ["warnings"],
    "contraindications": ["contraindications"],
    "adverse_reactions": ["adverse_reactions"],
    "active_ingredients": ["active_ingredients"],
    "metadata": ["manufacturer", "storage"],
}


def _gold_has_data(gold: dict[str, Any], dimension: str) -> bool:
    """Check whether the gold record has data for a scoring dimension."""
    fields = _GOLD_FIELD_MAP.get(dimension, [])
    for field in fields:
        val = gold.get(field)
        if val is None:
            continue
        if isinstance(val, (list, dict)) and len(val) > 0:
            return True
        if isinstance(val, str) and val.strip():
            return True
    return False


# ── Per-document scorer ───────────────────────────────────────────────


def score_document(
    candidate: dict[str, Any],
    gold: dict[str, Any],
) -> dict[str, float]:
    """Score a single document extraction against its gold answer.

    Returns per-dimension scores (0.0–1.0) and a weighted total.

    Dimensions where the gold has no data (empty list / empty string) are
    excluded from the weighted total — they neither reward nor penalize.
    The weight is redistributed proportionally among populated dimensions.
    """
    scores: dict[str, float] = {}

    # Always scored (drug_name is always populated in gold)
    scores["drug_name"] = score_drug_name(
        str(candidate.get("drug_name", "")),
        str(gold.get("drug_name", "")),
    )

    # List-based dimensions: score only when gold has data
    _list_dims: list[tuple[str, float]] = [
        (
            "indications",
            score_indications(
                candidate.get("indications") or [],
                gold.get("indications") or [],
            ),
        ),
        (
            "dosage_forms",
            score_dosage_forms(
                candidate.get("dosage_forms") or [],
                gold.get("dosage_forms") or [],
            ),
        ),
        (
            "warnings",
            score_warnings(
                candidate.get("warnings") or [],
                gold.get("warnings") or [],
            ),
        ),
        (
            "contraindications",
            score_contraindications(
                candidate.get("contraindications") or [],
                gold.get("contraindications") or [],
            ),
        ),
        (
            "adverse_reactions",
            score_adverse_reactions(
                candidate.get("adverse_reactions") or [],
                gold.get("adverse_reactions") or [],
            ),
        ),
        (
            "active_ingredients",
            score_active_ingredients(
                candidate.get("active_ingredients") or [],
                gold.get("active_ingredients") or [],
            ),
        ),
    ]
    for dim_name, dim_score in _list_dims:
        scores[dim_name] = dim_score

    scores["metadata"] = score_metadata(candidate, gold)

    # Compute weighted total, excluding dimensions where gold is empty.
    # Gold-empty dimensions get score = None for exclusion tracking, but
    # we use 0.0 in the per-document breakdown for consistency.
    active_weight = 0.0
    weighted_sum = 0.0
    for dim, weight in DIMENSION_WEIGHTS.items():
        gold_has_data = _gold_has_data(gold, dim)
        if gold_has_data:
            active_weight += weight
            weighted_sum += weight * scores[dim]

    total = weighted_sum / active_weight if active_weight > 0 else 0.0

    return {
        "drug_name": scores["drug_name"],
        "indications": scores["indications"],
        "dosage_forms": scores["dosage_forms"],
        "warnings": scores["warnings"],
        "contraindications": scores["contraindications"],
        "adverse_reactions": scores["adverse_reactions"],
        "active_ingredients": scores["active_ingredients"],
        "metadata": scores["metadata"],
        "total": total,
    }


# ── Full submission scorer ────────────────────────────────────────────


def score_submission(
    candidate_responses: Sequence[dict[str, Any]],
    gold_answers: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    """Score a full Task 2 submission and produce the final result.

    Matches candidates to golds by ``document_id``. Computes per-dimension
    mean scores across all documents, plus a weighted resolution score.

    Returns:
      - resolution: 0–100 weighted score
      - dimension_scores: per-dimension mean (0.0–1.0)
      - documents_scored / documents_errored
      - per_document: full per-document breakdown for error analysis
      - errors: list of document IDs that couldn't be scored
    """
    if not gold_answers:
        msg = "Gold answer set is empty"
        raise ValueError(msg)

    # Build lookup by document_id
    candidate_by_id = {str(c.get("document_id", "")): c for c in candidate_responses}

    per_document: list[dict[str, Any]] = []
    errors: list[str] = []

    # Per-dimension accumulators
    dim_totals: dict[str, float] = {dim: 0.0 for dim in DIMENSION_WEIGHTS}
    dim_counts: dict[str, int] = {dim: 0 for dim in DIMENSION_WEIGHTS}

    for gold in gold_answers:
        doc_id = str(gold.get("document_id", ""))
        candidate = candidate_by_id.get(doc_id)

        if candidate is None:
            errors.append(f"Missing response for document {doc_id}")
            doc_result = score_document({}, gold)
            doc_result["document_id"] = doc_id
            per_document.append(doc_result)
        else:
            doc_result = score_document(candidate, gold)
            doc_result["document_id"] = doc_id
            per_document.append(doc_result)

        for dim in DIMENSION_WEIGHTS:
            if _gold_has_data(gold, dim):
                dim_totals[dim] += doc_result[dim]
                dim_counts[dim] += 1

    n = len(gold_answers)

    # Mean per-dimension scores across only the documents where that dimension exists in gold.
    dimension_scores = {
        dim: round(dim_totals[dim] / dim_counts[dim], 4) if dim_counts[dim] > 0 else 0.0 for dim in DIMENSION_WEIGHTS
    }

    # Final resolution score is the mean of per-document totals.
    resolution = sum(doc["total"] for doc in per_document) / n * 100
    resolution = round(resolution, 1)

    return {
        "resolution": resolution,
        "documents_scored": n - len(errors),
        "documents_errored": len(errors),
        "dimension_scores": dimension_scores,
        "per_document": per_document,
        "errors": errors,
    }
