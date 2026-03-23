"""Creates the infra required to use Pulumi to manage an Azure subscription via GitHub Actions."""

import pulumi
import pulumi_azuread as azuread
from pulumi_azure_native import authorization
from pulumi_azure_native import resources
from pulumi_azure_native import storage

from src.roles import BuiltInRole
from src.settings import settings


def main() -> None:
    assert settings.GITHUB_ACTIONS, "This script should only be run in a GitHub Actions CI environment."

    # Get the resource group where the managed identity is located
    resource_group = resources.ResourceGroup.get(
        "github-actions-rg",
        id=resources.get_resource_group(
            settings.MANAGED_IDENTITY_RESOURCE_GROUP_NAME,
        ).id,
    )

    # Get the service principal for the managed identity
    service_principal = azuread.get_service_principal(
        client_id=settings.MANAGED_IDENTITY_CLIENT_ID,
    )

    # Create the storage account container that will serve as the Pulumi backend
    # in the same resource group as the managed identity.
    # https://www.pulumi.com/docs/iac/concepts/state-and-backends
    storage_account = storage.StorageAccount(
        "pulumi",
        resource_group_name=resource_group.name,
        location=resource_group.location,
        kind=storage.Kind.STORAGE_V2,
        sku=storage.SkuArgs(
            name=storage.SkuName.STANDARD_LRS,
        ),
        minimum_tls_version=storage.MinimumTlsVersion.TLS1_2,
        allow_blob_public_access=False,
    )

    storage_container = storage.BlobContainer(
        "backend",
        resource_group_name=resource_group.name,
        account_name=storage_account.name,
    )

    # Give the managed identity access to the blob container serving as the Pulumi backend
    authorization.RoleAssignment(
        "container-contributor",
        role_definition_id=BuiltInRole.STORAGE_BLOB_DATA_CONTRIBUTOR.to_definition_id(),
        principal_id=service_principal.object_id,
        principal_type=authorization.PrincipalType.SERVICE_PRINCIPAL,
        scope=storage_container.id,
    )

    pulumi.export("AZURE_TENANT_ID", settings.tenant_id)
    pulumi.export("AZURE_SUBSCRIPTION_ID", settings.subscription_id)
    pulumi.export("AZURE_CLIENT_ID", settings.MANAGED_IDENTITY_CLIENT_ID)
    pulumi.export("PULUMI_AZURE_STORAGE_ACCOUNT", storage_account.name)
    pulumi.export("PULUMI_AZURE_STORAGE_CONTAINER", storage_container.name)


main()
