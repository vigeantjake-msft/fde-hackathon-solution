from typing import Any

import pulumi
import pytest
from pulumi_azure_native import resources
from pulumi_azure_native import storage

from ms.infra.utils.vnet import StorageSubResource
from ms.infra.utils.vnet import create_storage_private_endpoints
from ms.infra.utils.vnet import deploy_private_dns_zones
from ms.infra.utils.vnet import deploy_vnet


class _VnetMocks(pulumi.runtime.Mocks):
    def __init__(self) -> None:
        self.created_resources: list[pulumi.runtime.MockResourceArgs] = []

    def new_resource(self, args: pulumi.runtime.MockResourceArgs):
        self.created_resources.append(args)
        outputs: dict[str, Any] = {
            **args.inputs,
            "id": f"/subscriptions/00000000-0000-0000-0000-000000000000/mock/{args.name}",
            "name": args.inputs.get("name", args.name),
            "location": args.inputs.get("location", "uksouth"),
        }
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
def vnet_mocks() -> _VnetMocks:
    mocks = _VnetMocks()
    pulumi.runtime.set_mocks(mocks, stack="dev-test")
    return mocks


def _make_rg() -> resources.ResourceGroup:
    return resources.ResourceGroup("rg", resource_group_name="test-rg", location="uksouth")


# ---------------------------------------------------------------------------
# Tests: deploy_vnet
# ---------------------------------------------------------------------------


class TestDeployVnet:
    @pulumi.runtime.test
    def test_creates_vnet_with_two_subnets(self, vnet_mocks: _VnetMocks) -> None:
        rg = _make_rg()
        result = deploy_vnet(rg, location="uksouth")

        def _assert(_: object) -> None:
            vnets = vnet_mocks.resources_of_type("network:virtualnetwork")
            subnets = vnet_mocks.resources_of_type("network:subnet")
            assert len(vnets) == 1
            assert len(subnets) == 2

        result.private_endpoints_subnet.id.apply(_assert)

    @pulumi.runtime.test
    def test_functions_subnet_has_web_delegation(self, vnet_mocks: _VnetMocks) -> None:
        rg = _make_rg()
        result = deploy_vnet(rg, location="uksouth")

        def _assert(_: object) -> None:
            subnets = vnet_mocks.resources_of_type("network:subnet")
            func_subnet = next(s for s in subnets if "functions" in s.name)
            delegations = func_subnet.inputs.get("delegations", [])
            assert len(delegations) == 1
            assert delegations[0]["serviceName"] == "Microsoft.Web/serverFarms"

        result.functions_subnet.id.apply(_assert)

    @pulumi.runtime.test
    def test_vnet_uses_custom_location_when_specified(self, vnet_mocks: _VnetMocks) -> None:
        rg = _make_rg()
        result = deploy_vnet(rg, location="swedencentral")

        def _assert(_: object) -> None:
            vnets = vnet_mocks.resources_of_type("network:virtualnetwork")
            assert vnets[0].inputs["location"] == "swedencentral"

        result.vnet.id.apply(_assert)


# ---------------------------------------------------------------------------
# Tests: deploy_private_dns_zones
# ---------------------------------------------------------------------------


class TestDeployPrivateDnsZones:
    @pulumi.runtime.test
    def test_creates_three_zones(self, vnet_mocks: _VnetMocks) -> None:
        rg = _make_rg()
        vnet_result = deploy_vnet(rg, location="uksouth")
        result = deploy_private_dns_zones(rg, vnet=vnet_result.vnet)

        def _assert(_: object) -> None:
            zones = vnet_mocks.resources_of_type("privatedns:privatezone")
            zone_names = {z.inputs.get("private_zone_name") or z.inputs.get("privateZoneName") for z in zones}
            assert zone_names == {
                "privatelink.blob.core.windows.net",
                "privatelink.queue.core.windows.net",
                "privatelink.table.core.windows.net",
            }

        result.table.id.apply(_assert)


# ---------------------------------------------------------------------------
# Tests: create_storage_private_endpoints
# ---------------------------------------------------------------------------


class TestCreateStoragePrivateEndpoints:
    @pulumi.runtime.test
    def test_creates_endpoints_for_each_group_id(self, vnet_mocks: _VnetMocks) -> None:
        rg = _make_rg()
        vnet_result = deploy_vnet(rg, location="uksouth")
        dns_zones = deploy_private_dns_zones(rg, vnet=vnet_result.vnet)
        sa = storage.StorageAccount(
            "test-sa",
            resource_group_name=rg.name,
            account_name="testsa",
            kind=storage.Kind.STORAGE_V2,
            sku=storage.SkuArgs(name=storage.SkuName.STANDARD_LRS),
        )

        endpoints = create_storage_private_endpoints(
            resource_group=rg,
            storage_account=sa,
            subnet=vnet_result.private_endpoints_subnet,
            dns_zones=dns_zones,
            sub_resources=list(StorageSubResource),
            name_prefix="durable",
            location="uksouth",
        )

        def _assert(_: object) -> None:
            pes = vnet_mocks.resources_of_type("network:privateendpoint")
            pe_names = {pe.name for pe in pes}
            assert "pe-durable-blob" in pe_names
            assert "pe-durable-queue" in pe_names
            assert "pe-durable-table" in pe_names

        endpoints[0].id.apply(_assert)

    @pulumi.runtime.test
    def test_single_group_id_creates_one_endpoint(self, vnet_mocks: _VnetMocks) -> None:
        rg = _make_rg()
        vnet_result = deploy_vnet(rg, location="uksouth")
        dns_zones = deploy_private_dns_zones(rg, vnet=vnet_result.vnet)
        sa = storage.StorageAccount(
            "test-sa",
            resource_group_name=rg.name,
            account_name="testsa",
            kind=storage.Kind.STORAGE_V2,
            sku=storage.SkuArgs(name=storage.SkuName.STANDARD_LRS),
        )

        endpoints = create_storage_private_endpoints(
            resource_group=rg,
            storage_account=sa,
            subnet=vnet_result.private_endpoints_subnet,
            dns_zones=dns_zones,
            sub_resources=[StorageSubResource.BLOB],
            name_prefix="dataset",
            location="uksouth",
        )

        assert len(endpoints) == 1

        def _assert(_: object) -> None:
            pes = vnet_mocks.resources_of_type("network:privateendpoint")
            pe_names = {pe.name for pe in pes}
            assert "pe-dataset-blob" in pe_names

        endpoints[0].id.apply(_assert)

    @pulumi.runtime.test
    def test_uses_custom_location_when_specified(self, vnet_mocks: _VnetMocks) -> None:
        rg = _make_rg()
        vnet_result = deploy_vnet(rg, location="swedencentral")
        dns_zones = deploy_private_dns_zones(rg, vnet=vnet_result.vnet)
        sa = storage.StorageAccount(
            "test-sa",
            resource_group_name=rg.name,
            account_name="testsa",
            kind=storage.Kind.STORAGE_V2,
            sku=storage.SkuArgs(name=storage.SkuName.STANDARD_LRS),
        )

        endpoints = create_storage_private_endpoints(
            resource_group=rg,
            storage_account=sa,
            subnet=vnet_result.private_endpoints_subnet,
            dns_zones=dns_zones,
            sub_resources=[StorageSubResource.BLOB],
            name_prefix="test",
            location="swedencentral",
        )

        def _assert(_: object) -> None:
            pes = vnet_mocks.resources_of_type("network:privateendpoint")
            assert pes[0].inputs["location"] == "swedencentral"

        endpoints[0].id.apply(_assert)

    @pulumi.runtime.test
    def test_raises_for_unsupported_group_ids(self, vnet_mocks: _VnetMocks) -> None:
        rg = _make_rg()
        vnet_result = deploy_vnet(rg, location="uksouth")
        dns_zones = deploy_private_dns_zones(rg, vnet=vnet_result.vnet)
        sa = storage.StorageAccount(
            "test-sa",
            resource_group_name=rg.name,
            account_name="testsa",
            kind=storage.Kind.STORAGE_V2,
            sku=storage.SkuArgs(name=storage.SkuName.STANDARD_LRS),
        )

        with pytest.raises(ValueError, match="Unsupported sub_resources"):
            create_storage_private_endpoints(
                resource_group=rg,
                storage_account=sa,
                subnet=vnet_result.private_endpoints_subnet,
                dns_zones=dns_zones,
                sub_resources=["blob", "file"],  # type: ignore[list-item]
                name_prefix="test",
                location="uksouth",
            )
