# Copyright (c) Microsoft. All rights reserved.
<<<<<<< HEAD
"""Shared pytest fixtures for evaluation tests."""

import pytest

from ms.evals.scenarios.base import EvalScenario
from ms.evals.scenarios.data_cleanup import build_data_cleanup_scenarios
from ms.evals.scenarios.responsible_ai import build_responsible_ai_scenarios


@pytest.fixture(scope="session")
def data_cleanup_scenarios() -> list[EvalScenario]:
    """All data cleanup evaluation scenarios."""
    return build_data_cleanup_scenarios()


@pytest.fixture(scope="session")
def responsible_ai_scenarios() -> list[EvalScenario]:
    """All responsible AI evaluation scenarios."""
    return build_responsible_ai_scenarios()


@pytest.fixture(scope="session")
def all_scenarios(
    data_cleanup_scenarios: list[EvalScenario],
    responsible_ai_scenarios: list[EvalScenario],
) -> list[EvalScenario]:
    """All evaluation scenarios combined."""
    return [*data_cleanup_scenarios, *responsible_ai_scenarios]
=======
"""Shared fixtures for evals tests."""

from pathlib import Path

import pytest

from ms.evals_core.framework.models.scenario import EvalScenario
from ms.evals_core.framework.models.scenario import ScenarioCategory
from ms.evals_core.framework.scenarios.registry import default_registry


@pytest.fixture
def data_dir() -> Path:
    """Path to the repo-root docs/data/tickets/ directory.

    Walks upward and picks the first ``docs/data/tickets/`` that lives
    directly beneath a repository root (identified by the presence of a
    ``.git`` entry).  This avoids accidentally matching an intermediate
    ``py/docs/data/tickets/`` directory that only contains a subset of
    the expected data files.
    """
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / ".git").exists():
            tickets_dir = parent / "docs" / "data" / "tickets"
            if tickets_dir.is_dir():
                return tickets_dir
    pytest.fail("Could not locate docs/data/tickets/ under the repository root")


@pytest.fixture()
def data_cleanup_scenarios() -> list[EvalScenario]:
    """Load all data cleanup scenarios."""
    import ms.evals_core.framework.scenarios.data_cleanup  # noqa: F401, PLC0415

    return default_registry.by_category(ScenarioCategory.DATA_CLEANUP)


@pytest.fixture()
def responsible_ai_scenarios() -> list[EvalScenario]:
    """Load all responsible AI scenarios."""
    import ms.evals_core.framework.scenarios.responsible_ai  # noqa: F401, PLC0415

    return default_registry.by_category(ScenarioCategory.RESPONSIBLE_AI)
>>>>>>> users/fde-platform-agent/fde-hiring-test-3/boyevche
