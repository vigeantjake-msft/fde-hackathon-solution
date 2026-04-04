# Copyright (c) Microsoft. All rights reserved.
"""Shared fixtures for evals tests."""

import pytest

from ms.evals.models.scenario import EvalScenario
from ms.evals.models.scenario import ScenarioCategory
from ms.evals.scenarios.registry import get_scenarios_by_category


@pytest.fixture()
def data_cleanup_scenarios() -> list[EvalScenario]:
    """Load all data cleanup scenarios."""
    # Importing the module triggers scenario registration.
    import ms.evals.scenarios.data_cleanup  # noqa: F401, PLC0415

    return get_scenarios_by_category(ScenarioCategory.DATA_CLEANUP)


@pytest.fixture()
def responsible_ai_scenarios() -> list[EvalScenario]:
    """Load all responsible AI scenarios."""
    import ms.evals.scenarios.responsible_ai  # noqa: F401, PLC0415

    return get_scenarios_by_category(ScenarioCategory.RESPONSIBLE_AI)
