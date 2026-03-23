"""Azure Storage Account utilities for infrastructure provisioning."""

from pulumi_azure_native import storage
from pulumi_azure_native.resources import ResourceGroup

from ms.infra.core.naming import generate_storage_account_name
from ms.infra.core.settings import settings


def create_storage_account_for_durable_function(
    resource_group: ResourceGroup,
    app_name: str,
) -> storage.StorageAccount:
    """Create storage account for Durable Function orchestration state.

    Returns the StorageAccount resource for identity-based auth binding.
    Shared key access is disabled; callers must use managed identity + RBAC.
    """
    storage_account_name = generate_storage_account_name(
        project_name=settings.project_name,
        stack_name=settings.stack_name_without_dev_prefix,
        app_name=app_name,
        subscription_id=settings.subscription_id,
    )

    storage_account = storage.StorageAccount(
        f"{app_name}-func-storage",
        account_name=storage_account_name,
        resource_group_name=resource_group.name,
        kind=storage.Kind.STORAGE_V2,
        sku=storage.SkuArgs(name=storage.SkuName.STANDARD_LRS),
        enable_https_traffic_only=True,
        minimum_tls_version=storage.MinimumTlsVersion.TLS1_2,
        allow_shared_key_access=False,
    )

    return storage_account
