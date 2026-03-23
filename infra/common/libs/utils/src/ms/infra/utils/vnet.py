"""VNet, subnet, private DNS zone, and private endpoint provisioning for Azure Functions."""

from enum import StrEnum

import pulumi
from pulumi_azure_native import network
from pulumi_azure_native import privatedns
from pulumi_azure_native import storage
from pulumi_azure_native.resources import ResourceGroup
from pydantic import ConfigDict

from ms.infra.core.models.base import FrozenBaseModel


class NetworkResult(FrozenBaseModel):
    """Result of deploying VNet + subnets."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    vnet: network.VirtualNetwork
    functions_subnet: network.Subnet
    private_endpoints_subnet: network.Subnet


class PrivateDnsZones(FrozenBaseModel):
    """Private DNS zones for storage sub-resources."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    blob: privatedns.PrivateZone
    queue: privatedns.PrivateZone
    table: privatedns.PrivateZone


class StorageSubResource(StrEnum):
    """Azure Private Link group IDs for storage account sub-resources."""

    BLOB = "blob"
    QUEUE = "queue"
    TABLE = "table"


def deploy_vnet(
    resource_group: ResourceGroup,
    location: str | pulumi.Output[str],
) -> NetworkResult:
    """Create a VNet with subnets for function app integration and private endpoints.

    The VNet uses 10.0.0.0/16 with:
    - 10.0.1.0/24 delegated to Microsoft.Web/serverFarms (function apps)
    - 10.0.2.0/24 for private endpoints

    Args:
        resource_group: The resource group to create the VNet in.
        location: Azure region for the VNet. Must match the function app's region
            for VNet integration to work.
    """
    vnet = network.VirtualNetwork(
        "vnet",
        resource_group_name=resource_group.name,
        location=location,
        address_space=network.AddressSpaceArgs(
            address_prefixes=["10.0.0.0/16"],
        ),
    )

    functions_subnet = network.Subnet(
        "subnet-functions",
        resource_group_name=resource_group.name,
        virtual_network_name=vnet.name,
        address_prefix="10.0.1.0/24",
        delegations=[
            network.DelegationArgs(
                name="delegation-web",
                service_name="Microsoft.Web/serverFarms",
            ),
        ],
    )

    private_endpoints_subnet = network.Subnet(
        "subnet-private-endpoints",
        resource_group_name=resource_group.name,
        virtual_network_name=vnet.name,
        address_prefix="10.0.2.0/24",
        opts=pulumi.ResourceOptions(depends_on=[functions_subnet]),
    )

    return NetworkResult(
        vnet=vnet,
        functions_subnet=functions_subnet,
        private_endpoints_subnet=private_endpoints_subnet,
    )


def deploy_private_dns_zones(
    resource_group: ResourceGroup,
    vnet: network.VirtualNetwork,
) -> PrivateDnsZones:
    """Create private DNS zones for blob, queue, and table storage and link them to the VNet."""
    zones: dict[str, privatedns.PrivateZone] = {}

    for sub_resource in StorageSubResource:
        zone = privatedns.PrivateZone(
            f"pdz-{sub_resource}",
            resource_group_name=resource_group.name,
            location="global",
            private_zone_name=f"privatelink.{sub_resource}.core.windows.net",
        )

        privatedns.VirtualNetworkLink(
            f"pdz-link-{sub_resource}",
            resource_group_name=resource_group.name,
            private_zone_name=zone.name,
            virtual_network=privatedns.SubResourceArgs(id=vnet.id),
            registration_enabled=False,
            location="global",
        )

        zones[sub_resource] = zone

    return PrivateDnsZones(
        blob=zones[StorageSubResource.BLOB],
        queue=zones[StorageSubResource.QUEUE],
        table=zones[StorageSubResource.TABLE],
    )


def create_storage_private_endpoints(
    resource_group: ResourceGroup,
    storage_account: storage.StorageAccount,
    subnet: network.Subnet,
    dns_zones: PrivateDnsZones,
    sub_resources: list[StorageSubResource],
    name_prefix: str,
    location: str | pulumi.Output[str],
) -> list[network.PrivateEndpoint]:
    """Create private endpoints for a storage account's sub-resources.

    Args:
        resource_group: The resource group for the endpoints.
        storage_account: The storage account to connect to.
        subnet: The subnet to place private endpoints in.
        dns_zones: Private DNS zones for automatic DNS registration.
        sub_resources: Storage sub-resources to create endpoints for.
        name_prefix: Prefix for resource names (e.g. "durable" or "dataset").
        location: Azure region for the endpoints. Must match the subnet's VNet region.
    """
    zone_map: dict[StorageSubResource, pulumi.Output[str]] = {
        StorageSubResource.BLOB: dns_zones.blob.id,
        StorageSubResource.QUEUE: dns_zones.queue.id,
        StorageSubResource.TABLE: dns_zones.table.id,
    }

    unsupported = set(sub_resources) - zone_map.keys()
    if unsupported:
        msg = f"Unsupported sub_resources: {unsupported}. Supported: {set(zone_map.keys())}"
        raise ValueError(msg)

    endpoints: list[network.PrivateEndpoint] = []

    for sub_resource in sub_resources:
        pe = network.PrivateEndpoint(
            f"pe-{name_prefix}-{sub_resource}",
            resource_group_name=resource_group.name,
            location=location,
            subnet=network.SubnetArgs(id=subnet.id),
            private_link_service_connections=[
                network.PrivateLinkServiceConnectionArgs(
                    name=f"plsc-{name_prefix}-{sub_resource}",
                    private_link_service_id=storage_account.id,
                    group_ids=[sub_resource],  # Azure API name for Private Link sub-resource targeting
                ),
            ],
        )

        network.PrivateDnsZoneGroup(
            f"pdzg-{name_prefix}-{sub_resource}",
            resource_group_name=resource_group.name,
            private_endpoint_name=pe.name,
            private_dns_zone_configs=[
                network.PrivateDnsZoneConfigArgs(
                    name=f"config-{sub_resource}",
                    private_dns_zone_id=zone_map[sub_resource],
                ),
            ],
        )

        endpoints.append(pe)

    return endpoints
