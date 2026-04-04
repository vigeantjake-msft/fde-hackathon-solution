# Copyright (c) Microsoft. All rights reserved.
<<<<<<< HEAD
"""Global scenario registry for evaluation scenarios.

Provides a central registry for all evaluation scenarios. Scenario modules
register their scenarios at import time using the ``register`` function.
"""
=======
"""Central registry for evaluation scenarios."""
>>>>>>> users/fde-platform-agent/fde-hiring-test-3/boyevche

from ms.evals.models.scenario import EvalScenario
from ms.evals.models.scenario import ScenarioCategory

<<<<<<< HEAD
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
=======

class ScenarioRegistry:
    """Thread-safe registry for evaluation scenarios.

    Scenarios register themselves by calling `registry.register(scenario)`.
    Consumers can retrieve all scenarios or filter by category/tags.
    """

    def __init__(self) -> None:
        self._scenarios: dict[str, EvalScenario] = {}

    def register(self, scenario: EvalScenario) -> None:
        """Register a scenario. Raises ValueError on duplicate IDs."""
        if scenario.scenario_id in self._scenarios:
            msg = f"Duplicate scenario ID: {scenario.scenario_id}"
            raise ValueError(msg)
        self._scenarios[scenario.scenario_id] = scenario

    def get(self, scenario_id: str) -> EvalScenario:
        """Get a scenario by ID. Raises KeyError if not found."""
        return self._scenarios[scenario_id]

    def all(self) -> list[EvalScenario]:
        """Return all registered scenarios, sorted by ID."""
        return sorted(self._scenarios.values(), key=lambda s: s.scenario_id)

    def by_category(self, category: ScenarioCategory) -> list[EvalScenario]:
        """Return scenarios filtered by category, sorted by ID."""
        return sorted(
            (s for s in self._scenarios.values() if s.category == category),
            key=lambda s: s.scenario_id,
        )

    def by_tag(self, tag: str) -> list[EvalScenario]:
        """Return scenarios that have the given tag, sorted by ID."""
        return sorted(
            (s for s in self._scenarios.values() if tag in s.tags),
            key=lambda s: s.scenario_id,
        )

    @property
    def count(self) -> int:
        """Total number of registered scenarios."""
        return len(self._scenarios)


# Module-level singleton registry
default_registry = ScenarioRegistry()
>>>>>>> users/fde-platform-agent/fde-hiring-test-3/boyevche
