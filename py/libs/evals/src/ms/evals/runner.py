# Copyright (c) Microsoft. All rights reserved.
"""Evaluation runner — sends eval cases to a triage endpoint and scores the responses.

Can be used programmatically or as a CLI:
    uv run python -m ms.evals.runner --endpoint http://localhost:8000 --suite all
"""

import argparse
import json
import sys
import time
from collections.abc import Sequence
from pathlib import Path

import httpx

from ms.evals.datasets import DATA_CLEANUP_CASES
from ms.evals.datasets import RESPONSIBLE_AI_CASES
from ms.evals.models import EvalCase
from ms.evals.models import EvalResult
from ms.evals.models import EvalSuite
from ms.evals.scoring import score_eval_suite

_SUITE_MAP: dict[str, tuple[EvalSuite, tuple[EvalCase, ...]]] = {
    "data_cleanup": (EvalSuite.DATA_CLEANUP, DATA_CLEANUP_CASES),
    "responsible_ai": (EvalSuite.RESPONSIBLE_AI, RESPONSIBLE_AI_CASES),
}


def _call_triage(client: httpx.Client, endpoint: str, ticket_payload: dict[str, object]) -> tuple[dict[str, object] | None, float]:
    """POST a ticket to /triage. Returns (parsed response or None, latency_ms)."""
    url = endpoint.rstrip("/") + "/triage"
    start = time.monotonic()
    try:
        resp = client.post(url, json=ticket_payload, timeout=30.0)
        elapsed_ms = (time.monotonic() - start) * 1000
        resp.raise_for_status()
        return resp.json(), elapsed_ms
    except Exception as exc:
        elapsed_ms = (time.monotonic() - start) * 1000
        print(f"  \u2717 {ticket_payload.get('ticket_id', '?')}: {exc}")
        return None, elapsed_ms


def _check_health(client: httpx.Client, endpoint: str) -> bool:
    """GET /health — returns True if 200."""
    url = endpoint.rstrip("/") + "/health"
    try:
        resp = client.get(url, timeout=10.0)
        return resp.status_code == 200
    except Exception:
        return False


def run_suite(
    endpoint: str,
    cases: Sequence[EvalCase],
    suite: EvalSuite,
    *,
    concurrency: int = 1,
) -> EvalResult:
    """Run an evaluation suite against a live endpoint and return scored results.

    Args:
        endpoint: Base URL of the triage service (e.g. http://localhost:8000).
        cases: The eval cases to run.
        suite: Which evaluation suite this is.
        concurrency: Number of parallel requests (default 1 for deterministic output).

    Returns:
        An EvalResult with full scoring breakdown.
    """
    client = httpx.Client()
    responses: list[dict[str, object]] = []
    latencies: list[float] = []

    for case in cases:
        ticket_payload = json.loads(case.ticket.model_dump_json())
        pred, elapsed_ms = _call_triage(client, endpoint, ticket_payload)
        latencies.append(elapsed_ms)

        if pred is None:
            responses.append({"ticket_id": case.ticket.ticket_id})
        else:
            responses.append(pred)

        # Per-ticket progress indicator
        status = "\u2713" if pred is not None else "\u2717"
        print(f"  {status} [{case.case_id}] {case.ticket.ticket_id} ({elapsed_ms:.0f}ms) — {case.description[:60]}")

    client.close()

    return score_eval_suite(suite, responses, list(cases))


def _print_result(result: EvalResult) -> None:
    """Pretty-print an evaluation result to stdout."""
    dim = result.dimension_scores
    print()
    print("=" * 65)
    print(f"  {result.suite.value.upper()} EVALUATION RESULTS")
    print("=" * 65)
    print()
    print("  Dimension scores:")
    print(f"    category        {dim.category:.4f}  (macro F1)")
    print(f"    priority        {dim.priority:.4f}  (mean partial credit)")
    print(f"    routing         {dim.routing:.4f}  (macro F1)")
    print(f"    missing_info    {dim.missing_info:.4f}  (mean set F1)")
    print(f"    escalation      {dim.escalation:.4f}  (binary F1)")
    print()
    print(f"  Classification score: {result.classification_score:.1f} / 85")
    print(f"  Tickets scored: {result.tickets_scored}")
    print(f"  Tickets errored: {result.tickets_errored}")

    if result.errors:
        print()
        print("  Errors:")
        for err in result.errors:
            print(f"    - {err}")

    # Per-ticket breakdown
    print()
    print("  Per-ticket breakdown:")
    print(f"    {'ticket_id':<20s} {'cat':>5s} {'pri':>5s} {'rte':>5s} {'miss':>5s} {'esc':>5s} {'total':>6s}")
    print(f"    {'─' * 20} {'─' * 5} {'─' * 5} {'─' * 5} {'─' * 5} {'─' * 5} {'─' * 6}")
    for ts in result.per_ticket:
        print(
            f"    {ts.ticket_id:<20s} {ts.category:5.2f} {ts.priority:5.2f} "
            f"{ts.routing:5.2f} {ts.missing_info:5.2f} {ts.escalation:5.2f} "
            f"{ts.weighted_total:6.4f}"
        )
    print()


def main() -> int:
    """CLI entry point for the evaluation runner."""
    parser = argparse.ArgumentParser(
        description="Run data-cleanup and/or responsible-AI evaluations against a triage endpoint.",
    )
    parser.add_argument(
        "--endpoint",
        required=True,
        help="Base URL of the triage service (e.g. http://localhost:8000)",
    )
    parser.add_argument(
        "--suite",
        choices=["data_cleanup", "responsible_ai", "all"],
        default="all",
        help="Which evaluation suite to run (default: all)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Path to write JSON results (optional)",
    )
    args = parser.parse_args()

    # Health check
    client = httpx.Client()
    healthy = _check_health(client, args.endpoint)
    client.close()
    print(f"Health check: {'\u2713 OK' if healthy else '\u2717 FAILED'}")
    if not healthy:
        print("Warning: GET /health did not return 200. Continuing anyway...")
    print()

    suites_to_run: list[tuple[EvalSuite, tuple[EvalCase, ...]]] = []
    if args.suite == "all":
        suites_to_run = list(_SUITE_MAP.values())
    else:
        suites_to_run = [_SUITE_MAP[args.suite]]

    all_results: list[EvalResult] = []
    for suite_enum, cases in suites_to_run:
        print(f"Running {suite_enum.value} suite ({len(cases)} cases)...")
        result = run_suite(args.endpoint, cases, suite_enum)
        _print_result(result)
        all_results.append(result)

    # Write JSON output
    if args.output:
        output_path = Path(args.output)
        output_data = [json.loads(r.model_dump_json()) for r in all_results]
        output_path.write_text(json.dumps(output_data, indent=2) + "\n")
        print(f"Results saved to {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
