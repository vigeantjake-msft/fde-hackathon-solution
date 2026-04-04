# Copyright (c) Microsoft. All rights reserved.
"""Export evaluation scenarios to JSON files for the eval harness.

Produces two JSON files per scenario category:
  - tickets file: list of input tickets (matches input.json schema)
  - gold file: list of expected triage decisions (matches output.json schema)
"""

import json
from pathlib import Path

from ms.evals.models.scenario import EvalScenario
from ms.evals.models.scenario import ScenarioCategory
from ms.evals.scenarios.registry import get_scenarios_by_category


def export_category_to_json(
    category: ScenarioCategory,
    tickets_path: Path,
    gold_path: Path,
) -> int:
    """Export all scenarios for a category to JSON ticket and gold files.

    Args:
        category: The scenario category to export.
        tickets_path: Path for the tickets JSON file.
        gold_path: Path for the gold answers JSON file.

    Returns:
        The number of scenarios exported.
    """
    scenarios = get_scenarios_by_category(category)
    tickets = [_scenario_to_ticket_dict(s) for s in scenarios]
    gold = [_scenario_to_gold_dict(s) for s in scenarios]

    tickets_path.parent.mkdir(parents=True, exist_ok=True)
    gold_path.parent.mkdir(parents=True, exist_ok=True)

    tickets_path.write_text(json.dumps(tickets, indent=4, ensure_ascii=False) + "\n")
    gold_path.write_text(json.dumps(gold, indent=4, ensure_ascii=False) + "\n")

    return len(scenarios)


def _scenario_to_ticket_dict(scenario: EvalScenario) -> dict[str, object]:
    """Convert a scenario's ticket to a JSON-serializable dict."""
    ticket = scenario.ticket
    result: dict[str, object] = {
        "ticket_id": ticket.ticket_id,
        "subject": ticket.subject,
        "description": ticket.description,
        "reporter": {
            "name": ticket.reporter.name,
            "email": ticket.reporter.email,
            "department": ticket.reporter.department,
        },
        "created_at": ticket.created_at,
        "channel": ticket.channel.value,
    }
    if ticket.attachments:
        result["attachments"] = ticket.attachments
    else:
        result["attachments"] = []
    return result


def _scenario_to_gold_dict(scenario: EvalScenario) -> dict[str, object]:
    """Convert a scenario's expected triage to a JSON-serializable dict."""
    expected = scenario.expected
    return {
        "ticket_id": expected.ticket_id,
        "category": expected.category.value,
        "priority": expected.priority.value,
        "assigned_team": expected.assigned_team.value,
        "needs_escalation": expected.needs_escalation,
        "missing_information": [m.value for m in expected.missing_information],
        "next_best_action": expected.next_best_action,
        "remediation_steps": list(expected.remediation_steps),
    }
