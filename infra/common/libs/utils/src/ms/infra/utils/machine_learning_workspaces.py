import pulumi_azuread as azuread
from pulumi_azure_native import applicationinsights
from pulumi_azure_native import authorization
from pulumi_azure_native import keyvault
from pulumi_azure_native import machinelearningservices
from pulumi_azure_native import operationalinsights
from pulumi_azure_native import storage
from pulumi_azure_native.resources import ResourceGroup

from ms.infra.core.settings import settings
from ms.infra.utils.roles import BuiltInRole


def deploy_eval_machine_learning_workspace(resource_group: ResourceGroup) -> machinelearningservices.Workspace | None:
    """
    Deploys an Azure Machine Learning workspace for running prompt evaluations.
    This is needed to access Responsible AI (RAI) tools like simulators and evaluators.
    """
    if not settings.is_staging_stack:
        return None

    github_actions_sp = azuread.get_service_principal(
        client_id=settings.client_id,
    )

    # Location **has** to be East US 2. This is the only region where the RAI evaluators are available.
    ml_workspace_location = "eastus2"

    ml_workspace = machinelearningservices.Workspace(
        "ml-workspace",
        resource_group_name=resource_group.name,
        location=ml_workspace_location,
        sku=machinelearningservices.SkuArgs(
            name=machinelearningservices.SkuTier.BASIC,
            tier=machinelearningservices.SkuTier.BASIC,
        ),
        identity=machinelearningservices.ManagedServiceIdentityArgs(
            type=machinelearningservices.ManagedServiceIdentityType.SYSTEM_ASSIGNED,
        ),
        storage_account=storage.StorageAccount(
            "mlsa",
            resource_group_name=resource_group.name,
            location=ml_workspace_location,
            kind=storage.Kind.STORAGE_V2,
            sku=storage.SkuArgs(
                name=storage.SkuName.STANDARD_LRS,
            ),
            minimum_tls_version=storage.MinimumTlsVersion.TLS1_2,
        ).id,
        key_vault=keyvault.Vault(
            "ml-vault",
            resource_group_name=resource_group.name,
            location=ml_workspace_location,
            properties=keyvault.VaultPropertiesArgs(
                tenant_id=settings.tenant_id,
                sku=keyvault.SkuArgs(
                    family=keyvault.SkuFamily.A,
                    name=keyvault.SkuName.STANDARD,
                ),
            ),
        ).id,
        application_insights=applicationinsights.Component(
            "ml-appinsights",
            resource_group_name=resource_group.name,
            location=ml_workspace_location,
            application_type=applicationinsights.ApplicationType.WEB,
            kind="web",
            ingestion_mode=applicationinsights.IngestionMode.LOG_ANALYTICS,
            workspace_resource_id=operationalinsights.Workspace(
                "ml-log-analytics",
                resource_group_name=resource_group.name,
                location=ml_workspace_location,
                sku=operationalinsights.WorkspaceSkuArgs(
                    name=operationalinsights.WorkspaceSkuNameEnum.PER_GB2018,
                ),
                retention_in_days=30,
            ).id,
        ).id,
    )

    # Give the GitHub Actions OIDC app access to the ML workspace
    authorization.RoleAssignment(
        "ra-github-actions-ml",
        role_definition_id=BuiltInRole.AZURE_AI_DEVELOPER.to_definition_id(),
        principal_id=github_actions_sp.object_id,
        principal_type=authorization.PrincipalType.SERVICE_PRINCIPAL,
        scope=ml_workspace.id,
    )

    return ml_workspace
