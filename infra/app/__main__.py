"""Pulumi IaC — deploys the FDEBench solution to Azure Container Apps.

Provisions (or reuses) all infrastructure in a single resource group:
  - Azure Container Registry (ACR) for Docker images
  - Azure OpenAI account with gpt-4-1-mini deployment
  - Log Analytics workspace
  - Container Apps managed environment
  - Container App (system-assigned identity, managed auth to ACR + OpenAI)

Usage:
    cd infra/app
    pulumi stack init jake-dev
    pulumi config set azure-native:location eastus2
    pulumi up

Required Pulumi config:
    azure-native:location   Azure region (default: eastus2)

The stack exports the deployed Container App FQDN so it can be passed to the
FDEBench submission portal as the API endpoint URL.
"""

import pulumi
import pulumi_azure_native as azure_native
from pulumi_azure_native import app as containerapp
from pulumi_azure_native import cognitiveservices
from pulumi_azure_native import containerregistry
from pulumi_azure_native import operationalinsights
from pulumi_azure_native import resources

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

config = pulumi.Config()
location = config.get("location") or "eastus2"
stack = pulumi.get_stack()
name_prefix = f"fdebench-{stack}"

# ---------------------------------------------------------------------------
# Resource group
# ---------------------------------------------------------------------------

rg = resources.ResourceGroup(
    f"{name_prefix}-rg",
    resource_group_name=f"rg-{name_prefix}",
    location=location,
)

# ---------------------------------------------------------------------------
# Azure Container Registry
# ---------------------------------------------------------------------------

acr = containerregistry.Registry(
    f"{name_prefix}-acr",
    resource_group_name=rg.name,
    location=rg.location,
    registry_name=f"{name_prefix.replace('-', '')}acr",
    sku=containerregistry.SkuArgs(name="Basic"),
    admin_user_enabled=False,
)

# ---------------------------------------------------------------------------
# Azure OpenAI
# ---------------------------------------------------------------------------

openai_account = cognitiveservices.Account(
    f"{name_prefix}-openai",
    resource_group_name=rg.name,
    location=rg.location,
    account_name=f"{name_prefix}-openai",
    kind="OpenAI",
    sku=cognitiveservices.SkuArgs(name="S0"),
    properties=cognitiveservices.AccountPropertiesArgs(
        custom_sub_domain_name=f"{name_prefix}-openai",
        disable_local_auth=True,  # keyless only
    ),
)

# Deploy gpt-4.1-mini (cost tier 0.9) with 50K TPM
model_deployment = cognitiveservices.Deployment(
    f"{name_prefix}-gpt-4-1-mini",
    resource_group_name=rg.name,
    account_name=openai_account.name,
    deployment_name="gpt-4-1-mini",
    properties=cognitiveservices.DeploymentPropertiesArgs(
        model=cognitiveservices.DeploymentModelArgs(
            format="OpenAI",
            name="gpt-4.1-mini",
            version="2025-04-14",
        ),
    ),
    sku=cognitiveservices.SkuArgs(
        name="GlobalStandard",
        capacity=50,
    ),
)

# ---------------------------------------------------------------------------
# Log Analytics + Container Apps Environment
# ---------------------------------------------------------------------------

log_workspace = operationalinsights.Workspace(
    f"{name_prefix}-logs",
    resource_group_name=rg.name,
    location=rg.location,
    workspace_name=f"{name_prefix}-logs",
    sku=operationalinsights.WorkspaceSkuArgs(name="PerGB2018"),
    retention_in_days=30,
)

workspace_keys = operationalinsights.get_shared_keys_output(
    resource_group_name=rg.name,
    workspace_name=log_workspace.name,
)

cae = containerapp.ManagedEnvironment(
    f"{name_prefix}-cae",
    resource_group_name=rg.name,
    location=rg.location,
    environment_name=f"{name_prefix}-cae",
    app_logs_configuration=containerapp.AppLogsConfigurationArgs(
        destination="log-analytics",
        log_analytics_configuration=containerapp.LogAnalyticsConfigurationArgs(
            customer_id=log_workspace.customer_id,
            shared_key=workspace_keys.primary_shared_key,
        ),
    ),
)

# ---------------------------------------------------------------------------
# Container App (system-assigned identity for keyless auth)
# ---------------------------------------------------------------------------

solution_app = containerapp.ContainerApp(
    f"{name_prefix}-app",
    resource_group_name=rg.name,
    container_app_name=f"{name_prefix}-app",
    location=rg.location,
    managed_environment_id=cae.id,
    identity=containerapp.ManagedServiceIdentityArgs(
        type="SystemAssigned",
    ),
    configuration=containerapp.ConfigurationArgs(
        ingress=containerapp.IngressArgs(
            external=True,
            target_port=8000,
        ),
        registries=[
            containerapp.RegistryCredentialsArgs(
                server=acr.login_server,
                identity="system",
            )
        ],
    ),
    template=containerapp.TemplateArgs(
        containers=[
            containerapp.ContainerArgs(
                name="solution",
                # Image is built and pushed separately via CI or `make deploy`
                image=acr.login_server.apply(
                    lambda server: f"{server}/fdebench-solution:latest"
                ),
                resources=containerapp.ContainerResourcesArgs(
                    cpu=2.0,
                    memory="4Gi",
                ),
                env=[
                    containerapp.EnvironmentVarArgs(
                        name="AZURE_OPENAI_ENDPOINT",
                        value=openai_account.properties.apply(
                            lambda p: p.endpoint or ""
                        ),
                    ),
                    containerapp.EnvironmentVarArgs(name="TRIAGE_MODEL", value="gpt-4-1-mini"),
                    containerapp.EnvironmentVarArgs(name="EXTRACT_MODEL", value="gpt-4-1-mini"),
                    containerapp.EnvironmentVarArgs(name="ORCHESTRATE_MODEL", value="gpt-4-1-mini"),
                    containerapp.EnvironmentVarArgs(name="AZURE_OPENAI_API_VERSION", value="2024-12-01-preview"),
                    containerapp.EnvironmentVarArgs(name="LOG_LEVEL", value="INFO"),
                ],
            )
        ],
        scale=containerapp.ScaleArgs(min_replicas=1, max_replicas=3),
    ),
)

# ---------------------------------------------------------------------------
# Role assignments (managed identity → ACR + OpenAI)
# ---------------------------------------------------------------------------

# Allow the Container App to pull images from ACR
acr_pull_assignment = azure_native.authorization.RoleAssignment(
    f"{name_prefix}-acr-pull",
    scope=acr.id,
    role_definition_id="/providers/Microsoft.Authorization/roleDefinitions/7f951dda-4ed3-4680-a7ca-43fe172d538d",  # AcrPull
    principal_id=solution_app.identity.apply(lambda i: i.principal_id),
    principal_type="ServicePrincipal",
)

# Allow the Container App to call Azure OpenAI
openai_user_assignment = azure_native.authorization.RoleAssignment(
    f"{name_prefix}-openai-user",
    scope=openai_account.id,
    role_definition_id="/providers/Microsoft.Authorization/roleDefinitions/5e0bd9bd-7b93-4f28-af87-19fc36ad1654",  # Cognitive Services OpenAI User
    principal_id=solution_app.identity.apply(lambda i: i.principal_id),
    principal_type="ServicePrincipal",
)

# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------

pulumi.export("resource_group", rg.name)
pulumi.export("acr_login_server", acr.login_server)
pulumi.export("openai_endpoint", openai_account.properties.apply(lambda p: p.endpoint))
pulumi.export(
    "api_endpoint",
    solution_app.configuration.apply(
        lambda c: f"https://{c.ingress.fqdn}" if c and c.ingress else "not-deployed"
    ),
)
