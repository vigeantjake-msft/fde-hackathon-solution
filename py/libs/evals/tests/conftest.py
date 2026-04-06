# Copyright (c) Microsoft. All rights reserved.
"""Shared test fixtures for evals tests."""

import pytest

from ms.evals.scenarios.data_cleanup import get_all_data_cleanup_scenarios
from ms.evals.scenarios.responsible_ai import get_all_responsible_ai_scenarios


@pytest.fixture()
def data_cleanup_scenarios():
    return get_all_data_cleanup_scenarios()


@pytest.fixture()
def responsible_ai_scenarios():
    return get_all_responsible_ai_scenarios()


@pytest.fixture()
def all_scenarios(data_cleanup_scenarios, responsible_ai_scenarios):
    return data_cleanup_scenarios + responsible_ai_scenarios
