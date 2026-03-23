import uuid
from typing import Any

import pulumi
import pytest

from ms.infra.core.test_utils.mock_settings import mock_settings_property


class MyMocks(pulumi.runtime.Mocks):
    def new_resource(
        self,
        args: pulumi.runtime.MockResourceArgs,
    ):
        outputs: dict[Any, Any] = {
            **args.inputs,
            "id": str(uuid.uuid4()),
            "name": args.name,
        }
        return args.name + "_id", outputs

    def call(
        self,
        args: pulumi.runtime.MockCallArgs,
    ):
        return {}


pulumi.runtime.set_mocks(MyMocks())

from ms.infra.utils.models.role_assignment_info import (  # noqa: E402 # imports need to be after mocks are set
    RoleAssignmentInfo,
)
from ms.infra.utils.roles import BuiltInRole  # noqa: E402 # imports need to be after mocks are set


@pytest.mark.parametrize(
    ("prefix", "name", "expected_name"),
    [
        pytest.param(
            None,
            "test-role-assignment",
            "test-role-assignment",
            id="without-prefix",
        ),
        pytest.param(
            "myprefix",
            "test-role-assignment",
            "myprefix-test-role-assignment",
            id="with-prefix",
        ),
    ],
)
@mock_settings_property("subscription_id", "test-sub-id")
@pulumi.runtime.test
def test_role_assignment_info(
    prefix: str | None,
    name: str,
    expected_name: str,
) -> None:
    info = RoleAssignmentInfo(
        name=name,
        role=BuiltInRole.READER,
        scope="test-scope",
    )

    ra = info.create_service_principal_role_assignment(
        principal_id="test-principal-id",
        prefix=prefix,
    )

    def _assert(args: dict[str, str]) -> None:
        assert args["name"] == expected_name
        assert args["role_definition_id"] == BuiltInRole.READER.to_definition_id()
        assert args["principal_id"] == "test-principal-id"
        assert args["principal_type"] == "ServicePrincipal"
        assert args["scope"] == "test-scope"

    pulumi.Output.all(
        name=ra.name,
        role_definition_id=ra.role_definition_id,
        principal_id=ra.principal_id,
        principal_type=ra.principal_type,
        scope=ra.scope,
    ).apply(_assert)
