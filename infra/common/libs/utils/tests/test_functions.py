import uuid
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock
from unittest.mock import patch

import pulumi
import pytest
from pulumi_azure_native import containerregistry
from pulumi_azure_native import network
from pulumi_azure_native import privatedns
from pulumi_azure_native import resources
from pulumi_azure_native import web
from pulumi_command import local as command

from ms.infra.utils.functions import create_single_azure_function
from ms.infra.utils.models.azure_function import AzureFunction
from ms.infra.utils.vnet import PrivateDnsZones
from ms.infra.utils.vnet import StorageSubResource

# Pulumi wraps dicts containing secret values with this sigil key.
_SECRET_SIGIL = "4dabf18193072939515e22adb298388d"


# ---------------------------------------------------------------------------
# Pulumi mock infrastructure
# ---------------------------------------------------------------------------


class _FunctionMocks(pulumi.runtime.Mocks):
    """Pulumi mocks that track all created resources."""

    def __init__(self) -> None:
        self.created_resources: list[pulumi.runtime.MockResourceArgs] = []

    def new_resource(self, args: pulumi.runtime.MockResourceArgs):
        self.created_resources.append(args)

        outputs: dict[str, Any] = {
            **args.inputs,
            "id": f"/subscriptions/00000000-0000-0000-0000-000000000000/mock/{args.name}",
        }

        if args.typ.endswith(":resources:ResourceGroup"):
            name_keys = ("resource_group_name", "resourceGroupName")
        elif args.typ.endswith(":storage:StorageAccount"):
            name_keys = ("account_name", "accountName")
        elif args.typ.endswith(":web:WebApp"):
            outputs["identity"] = {
                "principalId": "mock-principal-id",
                "tenantId": "mock-tenant-id",
                "type": "SystemAssigned",
            }
            outputs["defaultHostName"] = f"{args.name}.azurewebsites.net"
            name_keys = ()
        elif args.typ.endswith(":containerregistry:Registry"):
            outputs["loginServer"] = "mockacr.azurecr.io"
            name_keys = ()
        elif args.typ.endswith(":local:Command"):
            # Echo back the command as stdout for testing purposes
            outputs["stdout"] = args.inputs.get("create", "")
            name_keys = ()
        elif args.typ == "docker-build:index:Image":
            tags = args.inputs.get("tags", [])
            outputs["ref"] = tags[0] if tags else f"mockacr.azurecr.io/{args.name}:latest"
            name_keys = ()
        else:
            name_keys = ()

        outputs["name"] = next(
            (args.inputs[k] for k in name_keys if k in args.inputs),
            args.inputs.get("name", args.name),
        )
        outputs["location"] = args.inputs.get("location", "SwedenCentral")
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

    def resources_of_type(self, type_fragment: str) -> list[pulumi.runtime.MockResourceArgs]:
        fragment = type_fragment.lower()
        return [r for r in self.created_resources if fragment in r.typ.lower()]


@pytest.fixture
def function_mocks() -> _FunctionMocks:
    mocks = _FunctionMocks()
    pulumi.runtime.set_mocks(mocks, stack="dev-test")
    return mocks


# ---------------------------------------------------------------------------
# Shared helpers & constants
# ---------------------------------------------------------------------------

_VALID_FUNCTION_ARGS: dict[str, Any] = {
    "app_name": "test-func",
    "dockerfile_path": "infra/docker/fastapi/azure-function/Dockerfile",
    "docker_build_context": "py",
    "app_path": "apps/test-func",
    "libs_path": "libs",
    "plan": "test-plan",
}


def _make_infra(
    function_mocks: _FunctionMocks,
) -> tuple[resources.ResourceGroup, web.AppServicePlan, containerregistry.Registry, command.Command]:
    rg = resources.ResourceGroup("rg", resource_group_name="test-rg", location="SwedenCentral")
    plan = web.AppServicePlan(
        "asp-test",
        resource_group_name=rg.name,
        location="SwedenCentral",
        kind="FunctionApp",
        reserved=True,
        maximum_elastic_worker_count=1,
        sku=web.SkuDescriptionArgs(name="EP1", tier="ElasticPremium"),
    )
    acr = containerregistry.Registry(
        "acr",
        resource_group_name=rg.name,
        sku=containerregistry.SkuArgs(name="Standard"),
    )
    acr_login = command.Command("acr-login", create="echo ok", triggers=[str(uuid.uuid4())])
    return rg, plan, acr, acr_login


def _find_webapp(mocks: _FunctionMocks) -> pulumi.runtime.MockResourceArgs:
    webapps = mocks.resources_of_type("web:webapp")
    result = next((w for w in webapps if "fastapi-func" in w.name), None)
    assert result is not None, f"No WebApp found in: {[w.name for w in webapps]}"
    return result


def _unwrap_secret(value: Any) -> Any:
    """Unwrap Pulumi secret-wrapped dicts to access the underlying value."""
    if isinstance(value, dict) and _SECRET_SIGIL in value:
        return value["value"]
    return value


def _get_app_settings_dict(webapp: pulumi.runtime.MockResourceArgs) -> dict[str, Any]:
    raw_site_config = webapp.inputs.get("site_config") or webapp.inputs.get("siteConfig") or {}
    site_config = _unwrap_secret(raw_site_config)
    app_settings = site_config.get("app_settings") or site_config.get("appSettings") or []
    return {s["name"]: s["value"] for s in app_settings}


# ---------------------------------------------------------------------------
# Tests: durable function creates storage account and identity-based env vars
# ---------------------------------------------------------------------------
# Assertions on WebApp inputs (available when the WebApp resolves).
# Role assignments (created AFTER WebApp via depends_on) are tested
# separately below using mock.patch, since Pulumi's async mock runtime
# doesn't guarantee they're visible in a WebApp output apply callback.


class TestDurableFunctionStorageConfig:
    @pulumi.runtime.test
    @patch.object(Path, "is_file", return_value=True)
    def test_creates_storage_account(
        self,
        _mock_is_file: object,
        function_mocks: _FunctionMocks,
    ) -> None:
        rg, plan, acr, acr_login = _make_infra(function_mocks)

        result = create_single_azure_function(
            function=AzureFunction(**_VALID_FUNCTION_ARGS, is_durable=True),
            resource_group=rg,
            plan=plan,
            acr=acr,
            acr_login=acr_login,
        )

        def _assert(_: object) -> None:
            storage_accounts = function_mocks.resources_of_type("storage:storageaccount")
            assert len(storage_accounts) == 1

        result.id.apply(_assert)

    @patch.object(Path, "is_file", return_value=True)
    @patch("ms.infra.utils.functions.web.WebApp", wraps=web.WebApp)
    @pulumi.runtime.test
    def test_sets_identity_based_env_vars(
        self,
        mock_webapp: MagicMock,
        _mock_is_file: object,
        function_mocks: _FunctionMocks,
    ) -> None:
        rg, plan, acr, acr_login = _make_infra(function_mocks)

        create_single_azure_function(
            function=AzureFunction(**_VALID_FUNCTION_ARGS, is_durable=True),
            resource_group=rg,
            plan=plan,
            acr=acr,
            acr_login=acr_login,
        )

        _, kwargs = mock_webapp.call_args
        site_config = kwargs["site_config"]
        app_settings_args = site_config.app_settings
        names = {s.name for s in app_settings_args}
        assert "AzureWebJobsStorage__accountName" in names
        assert "AzureWebJobsStorage__credential" in names

        cred_setting = next(s for s in app_settings_args if s.name == "AzureWebJobsStorage__credential")
        assert cred_setting.value == "managedidentity"


class TestNonDurableFunctionSkipsStorage:
    @pulumi.runtime.test
    @patch.object(Path, "is_file", return_value=True)
    def test_no_storage_account_created(
        self,
        _mock_is_file: object,
        function_mocks: _FunctionMocks,
    ) -> None:
        rg, plan, acr, acr_login = _make_infra(function_mocks)

        result = create_single_azure_function(
            function=AzureFunction(**_VALID_FUNCTION_ARGS, is_durable=False),
            resource_group=rg,
            plan=plan,
            acr=acr,
            acr_login=acr_login,
        )

        def _assert(_: object) -> None:
            assert len(function_mocks.resources_of_type("storage:storageaccount")) == 0

        result.id.apply(_assert)

    @patch.object(Path, "is_file", return_value=True)
    @patch("ms.infra.utils.functions.web.WebApp", wraps=web.WebApp)
    @pulumi.runtime.test
    def test_no_storage_env_vars(
        self,
        mock_webapp: MagicMock,
        _mock_is_file: object,
        function_mocks: _FunctionMocks,
    ) -> None:
        rg, plan, acr, acr_login = _make_infra(function_mocks)

        create_single_azure_function(
            function=AzureFunction(**_VALID_FUNCTION_ARGS, is_durable=False),
            resource_group=rg,
            plan=plan,
            acr=acr,
            acr_login=acr_login,
        )

        _, kwargs = mock_webapp.call_args
        site_config = kwargs["site_config"]
        app_settings_args = site_config.app_settings
        names = {s.name for s in app_settings_args}
        assert "AzureWebJobsStorage__accountName" not in names
        assert "AzureWebJobsStorage__credential" not in names


# ---------------------------------------------------------------------------
# Tests: RBAC role assignments for durable function storage
# ---------------------------------------------------------------------------
# Role assignments depend on func.identity.principal_id (an Output that
# resolves asynchronously after the WebApp). Pulumi's mock runtime doesn't
# guarantee they appear in created_resources during a WebApp output callback.
# We use mock.patch on authorization.RoleAssignment to capture the calls
# directly — this tests the durable contract ("3 storage roles are created
# with the correct built-in role IDs") without coupling to Pulumi scheduling.


class TestDurableFunctionStorageRoleAssignments:
    @patch.object(Path, "is_file", return_value=True)
    @patch("ms.infra.utils.functions.authorization.RoleAssignment")
    @pulumi.runtime.test
    def test_creates_three_storage_role_assignments(
        self,
        mock_role_assignment: MagicMock,
        _mock_is_file: object,
        function_mocks: _FunctionMocks,
    ) -> None:
        rg, plan, acr, acr_login = _make_infra(function_mocks)

        result = create_single_azure_function(
            function=AzureFunction(**_VALID_FUNCTION_ARGS, is_durable=True),
            resource_group=rg,
            plan=plan,
            acr=acr,
            acr_login=acr_login,
        )

        def _assert(_: object) -> None:
            storage_calls = [c for c in mock_role_assignment.call_args_list if "storage" in str(c.args[0])]
            assert len(storage_calls) == 3

            actual_names = {c.args[0] for c in storage_calls}
            expected_names = {
                "ra-test-func-storage-blob",
                "ra-test-func-storage-queue",
                "ra-test-func-storage-table",
            }
            assert actual_names == expected_names

        result.id.apply(_assert)

    @patch.object(Path, "is_file", return_value=True)
    @patch("ms.infra.utils.functions.authorization.RoleAssignment")
    @pulumi.runtime.test
    def test_no_storage_roles_for_non_durable(
        self,
        mock_role_assignment: MagicMock,
        _mock_is_file: object,
        function_mocks: _FunctionMocks,
    ) -> None:
        rg, plan, acr, acr_login = _make_infra(function_mocks)

        result = create_single_azure_function(
            function=AzureFunction(**_VALID_FUNCTION_ARGS, is_durable=False),
            resource_group=rg,
            plan=plan,
            acr=acr,
            acr_login=acr_login,
        )

        def _assert(_: object) -> None:
            storage_calls = [c for c in mock_role_assignment.call_args_list if "storage" in str(c.args[0])]
            assert len(storage_calls) == 0

        result.id.apply(_assert)


# ---------------------------------------------------------------------------
# Tests: WebApp location co-location with App Service Plan
# ---------------------------------------------------------------------------


class TestWebAppLocationMatchesPlan:
    @pulumi.runtime.test
    @patch.object(Path, "is_file", return_value=True)
    def test_webapp_location_matches_plan(
        self,
        _mock_is_file: object,
        function_mocks: _FunctionMocks,
    ) -> None:
        rg, plan, acr, acr_login = _make_infra(function_mocks)

        result = create_single_azure_function(
            function=AzureFunction(**_VALID_FUNCTION_ARGS, is_durable=False),
            resource_group=rg,
            plan=plan,
            acr=acr,
            acr_login=acr_login,
        )

        def _assert(_: object) -> None:
            webapp = _find_webapp(function_mocks)
            assert webapp.inputs.get("location") == "SwedenCentral"

        result.id.apply(_assert)


# ---------------------------------------------------------------------------
# Tests: Easy Auth enforcement
# ---------------------------------------------------------------------------


class TestEasyAuthEnforcement:
    @pulumi.runtime.test
    @patch.object(Path, "is_file", return_value=True)
    def test_dev_stack_allows_missing_easy_auth(
        self,
        _mock_is_file: object,
        function_mocks: _FunctionMocks,
    ) -> None:
        rg, plan, acr, acr_login = _make_infra(function_mocks)

        result = create_single_azure_function(
            function=AzureFunction(**_VALID_FUNCTION_ARGS, is_durable=False),
            resource_group=rg,
            plan=plan,
            acr=acr,
            acr_login=acr_login,
        )

        def _assert(_: object) -> None:
            assert _find_webapp(function_mocks) is not None

        result.id.apply(_assert)

    @patch.object(Path, "is_file", return_value=True)
    def test_non_dev_stack_rejects_missing_easy_auth(
        self,
        _mock_is_file: object,
    ) -> None:
        mocks = _FunctionMocks()
        pulumi.runtime.set_mocks(mocks, stack="staging")

        rg, plan, acr, acr_login = _make_infra(mocks)

        with pytest.raises(AssertionError, match="Easy Auth Client ID is required"):
            create_single_azure_function(
                function=AzureFunction(**_VALID_FUNCTION_ARGS, is_durable=False),
                resource_group=rg,
                plan=plan,
                acr=acr,
                acr_login=acr_login,
            )


# ---------------------------------------------------------------------------
# Tests: VNet integration
# ---------------------------------------------------------------------------


class TestVnetIntegration:
    @patch.object(Path, "is_file", return_value=True)
    @patch("ms.infra.utils.functions.web.WebApp", wraps=web.WebApp)
    @pulumi.runtime.test
    def test_enables_vnet_integration_when_subnet_provided(
        self,
        mock_webapp: MagicMock,
        _mock_is_file: object,
        function_mocks: _FunctionMocks,
    ) -> None:
        rg, plan, acr, acr_login = _make_infra(function_mocks)

        create_single_azure_function(
            function=AzureFunction(**_VALID_FUNCTION_ARGS, is_durable=False),
            resource_group=rg,
            plan=plan,
            acr=acr,
            acr_login=acr_login,
            vnet_subnet_id=pulumi.Output.from_input("/subscriptions/mock/subnet-functions"),
        )

        _, kwargs = mock_webapp.call_args
        assert kwargs["virtual_network_subnet_id"] is not None
        assert kwargs["site_config"].vnet_route_all_enabled is True

        app_settings = kwargs["site_config"].app_settings
        names = {s.name for s in app_settings}
        assert "WEBSITE_VNET_ROUTE_ALL" in names
        assert "WEBSITE_DNS_SERVER" in names
        assert "WEBSITE_PULL_IMAGE_OVER_VNET" in names

        dns_setting = next(s for s in app_settings if s.name == "WEBSITE_DNS_SERVER")
        assert dns_setting.value == "168.63.129.16"

    @patch.object(Path, "is_file", return_value=True)
    @patch("ms.infra.utils.functions.web.WebApp", wraps=web.WebApp)
    @pulumi.runtime.test
    def test_no_vnet_config_without_subnet(
        self,
        mock_webapp: MagicMock,
        _mock_is_file: object,
        function_mocks: _FunctionMocks,
    ) -> None:
        rg, plan, acr, acr_login = _make_infra(function_mocks)

        create_single_azure_function(
            function=AzureFunction(**_VALID_FUNCTION_ARGS, is_durable=False),
            resource_group=rg,
            plan=plan,
            acr=acr,
            acr_login=acr_login,
        )

        _, kwargs = mock_webapp.call_args
        assert kwargs["virtual_network_subnet_id"] is None
        assert kwargs["site_config"].vnet_route_all_enabled is False

        app_settings = kwargs["site_config"].app_settings
        names = {s.name for s in app_settings}
        assert "WEBSITE_VNET_ROUTE_ALL" not in names
        assert "WEBSITE_DNS_SERVER" not in names
        assert "WEBSITE_PULL_IMAGE_OVER_VNET" not in names


class TestDurableFunctionPrivateEndpoints:
    @patch.object(Path, "is_file", return_value=True)
    @patch("ms.infra.utils.functions.create_storage_private_endpoints")
    @pulumi.runtime.test
    def test_creates_private_endpoints_for_durable_storage(
        self,
        mock_create_pe: MagicMock,
        _mock_is_file: object,
        function_mocks: _FunctionMocks,
    ) -> None:
        rg, plan, acr, acr_login = _make_infra(function_mocks)

        pe_subnet = network.Subnet(
            "subnet-pe",
            resource_group_name=rg.name,
            virtual_network_name="mock-vnet",
            address_prefix="10.0.2.0/24",
        )

        blob_zone = privatedns.PrivateZone("pdz-blob", resource_group_name=rg.name, location="global")
        queue_zone = privatedns.PrivateZone("pdz-queue", resource_group_name=rg.name, location="global")
        table_zone = privatedns.PrivateZone("pdz-table", resource_group_name=rg.name, location="global")

        dns_zones = PrivateDnsZones(blob=blob_zone, queue=queue_zone, table=table_zone)

        result = create_single_azure_function(
            function=AzureFunction(**_VALID_FUNCTION_ARGS, is_durable=True),
            resource_group=rg,
            plan=plan,
            acr=acr,
            acr_login=acr_login,
            private_endpoints_subnet=pe_subnet,
            private_dns_zones=dns_zones,
        )

        def _assert(_: object) -> None:
            mock_create_pe.assert_called_once()
            _, kwargs = mock_create_pe.call_args
            assert kwargs["sub_resources"] == list(StorageSubResource)
            assert "durable" in kwargs["name_prefix"]

        result.id.apply(_assert)

    @patch.object(Path, "is_file", return_value=True)
    @patch("ms.infra.utils.functions.create_storage_private_endpoints")
    @pulumi.runtime.test
    def test_no_private_endpoints_when_vnet_params_absent(
        self,
        mock_create_pe: MagicMock,
        _mock_is_file: object,
        function_mocks: _FunctionMocks,
    ) -> None:
        rg, plan, acr, acr_login = _make_infra(function_mocks)

        result = create_single_azure_function(
            function=AzureFunction(**_VALID_FUNCTION_ARGS, is_durable=True),
            resource_group=rg,
            plan=plan,
            acr=acr,
            acr_login=acr_login,
        )

        def _assert(_: object) -> None:
            mock_create_pe.assert_not_called()

        result.id.apply(_assert)
