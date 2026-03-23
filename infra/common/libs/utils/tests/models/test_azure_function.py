from typing import Any

import pytest

from ms.infra.utils.models.azure_function import AzureFunction


def test_plan_is_required() -> None:
    with pytest.raises(ValueError):
        AzureFunction(  # type: ignore[call-arg]
            app_name="test-func",
            dockerfile_path="Dockerfile",
            docker_build_context="py",
            app_path="apps/test-func",
        )


_VALID_FUNCTION_ARGS: dict[str, Any] = {
    "app_name": "test-func",
    "dockerfile_path": "Dockerfile",
    "docker_build_context": "py",
    "app_path": "apps/test-func",
    "plan": "my-plan",
}


def test_is_durable_defaults_to_false() -> None:
    assert AzureFunction(**_VALID_FUNCTION_ARGS).is_durable is False


def test_runtime_scale_monitoring_defaults_to_true() -> None:
    assert AzureFunction(**_VALID_FUNCTION_ARGS).runtime_scale_monitoring_enabled is True
