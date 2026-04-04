# Copyright (c) Microsoft. All rights reserved.
"""Global scenario registry for evaluation scenarios.

Provides a central registry for all evaluation scenarios. Scenario modules
register their scenarios at import time using the ``register`` function.
"""

from ms.evals.models.scenario import EvalScenario
from ms.evals.models.scenario import ScenarioCategory

_REGISTRY: dict[str, EvalScenario] = {}


def register(scenario: EvalScenario) -> EvalScenario:
    """Register an evaluation scenario in the global registry.

    Args:
        scenario: The evaluation scenario to register.

    Returns:
        The registered scenario (for chaining).

    Raises:
        ValueError: If a scenario with the same ID is already registered.
    """
    scenario_id = scenario.metadata.scenario_id
    if scenario_id in _REGISTRY:
        msg = f"Duplicate scenario ID: {scenario_id}"
        raise ValueError(msg)
    _REGISTRY[scenario_id] = scenario
    return scenario


def get_scenarios() -> list[EvalScenario]:
    """Return all registered scenarios, sorted by scenario ID."""
    return sorted(_REGISTRY.values(), key=lambda s: s.metadata.scenario_id)


def get_scenarios_by_category(category: ScenarioCategory) -> list[EvalScenario]:
    """Return all registered scenarios for a given category, sorted by scenario ID."""
    return sorted(
        (s for s in _REGISTRY.values() if s.metadata.category == category),
        key=lambda s: s.metadata.scenario_id,
    )
