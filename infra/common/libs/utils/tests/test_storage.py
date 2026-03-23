import uuid

import pulumi
import pytest
from pulumi_azure_native import resources
from pulumi_azure_native import storage

from ms.infra.core.naming import generate_storage_account_name
from ms.infra.core.settings import settings
from ms.infra.utils.storage import create_storage_account_for_durable_function


class _StorageMocks(pulumi.runtime.Mocks):
    """Pulumi mocks for storage account tests."""

    def __init__(self) -> None:
        self.created_resources: list[pulumi.runtime.MockResourceArgs] = []

    def new_resource(self, args: pulumi.runtime.MockResourceArgs):
        self.created_resources.append(args)

        outputs = {
            **args.inputs,
            "id": str(uuid.uuid4()),
        }

        # For azure-native resources, `name` is an output property.
        # Map it to the resource-type-specific input name.
        if args.typ.endswith(":resources:ResourceGroup"):
            name_keys = ("resource_group_name", "resourceGroupName")
        elif args.typ.endswith(":storage:StorageAccount"):
            name_keys = ("account_name", "accountName")
        else:
            name_keys = ()

        outputs["name"] = next(
            (args.inputs[k] for k in name_keys if k in args.inputs),
            args.inputs.get("name", args.name),
        )
        return args.name + "_id", outputs

    def call(self, args: pulumi.runtime.MockCallArgs) -> tuple[dict, list[tuple[str, str]]]:
        if args.token.endswith(":authorization:getClientConfig"):
            return {
                "clientId": "00000000-1234-0000-0000-000000000000",
                "objectId": "00000000-0000-1234-0000-000000000000",
                "subscriptionId": "00000000-0000-0000-1234-000000000000",
                "tenantId": "mock-tenant-id",
            }, []
        return {}, []


@pytest.fixture
def storage_mocks() -> _StorageMocks:
    mocks = _StorageMocks()
    pulumi.runtime.set_mocks(mocks)
    return mocks


def _find_created_resource(
    mocks: _StorageMocks,
    type_fragment: str,
) -> pulumi.runtime.MockResourceArgs | None:
    """Return the first created resource whose type contains the fragment (case-insensitive)."""
    fragment = type_fragment.lower()
    return next((r for r in mocks.created_resources if fragment in r.typ.lower()), None)


def test_generate_storage_account_name_meets_azure_constraints() -> None:
    result = generate_storage_account_name(
        project_name="fde",
        stack_name="test",
        app_name="sample-durable-function",
        subscription_id="00000000-0000-0000-0000-000000000000",
    )

    assert 3 <= len(result) <= 24
    assert result.isalnum()
    assert result.islower()
    assert result.startswith("st")


@pulumi.runtime.test
def test_create_storage_account_for_durable_function_config_and_outputs(
    storage_mocks: _StorageMocks,
) -> None:
    # Validates that the helper provisions a correctly configured storage account
    # and returns the StorageAccount resource (identity-based auth, no shared keys).
    rg_name = "rg-dev_test--with$$chars"
    app_name = "sample-durable-function"

    resource_group = resources.ResourceGroup(
        "rg",
        resource_group_name=rg_name,
        location="westus",
    )

    result = create_storage_account_for_durable_function(
        resource_group,
        app_name,
    )
    expected_account_name = generate_storage_account_name(
        project_name=pulumi.get_project(),
        stack_name=settings.stack_name_without_dev_prefix,
        app_name=app_name,
        subscription_id=settings.subscription_id,
    )

    assert isinstance(result, storage.StorageAccount)

    def _assert_all(_: object) -> None:
        def _get(inputs_dict: dict, *keys: str):
            for key in keys:
                if key in inputs_dict:
                    return inputs_dict[key]
            raise AssertionError(f"Expected one of keys {keys} in inputs: {sorted(inputs_dict.keys())}")

        storage_account_args = _find_created_resource(storage_mocks, "storage:storageaccount")
        assert storage_account_args is not None, [r.typ for r in storage_mocks.created_resources]

        inputs = storage_account_args.inputs
        assert _get(inputs, "account_name", "accountName") == expected_account_name
        assert _get(inputs, "enable_https_traffic_only", "enableHttpsTrafficOnly") is True
        assert _get(inputs, "minimum_tls_version", "minimumTlsVersion") == "TLS1_2"
        assert _get(inputs, "allow_shared_key_access", "allowSharedKeyAccess") is False

    result.name.apply(_assert_all)
