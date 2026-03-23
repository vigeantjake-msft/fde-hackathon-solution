from typing import Any

import pulumi
from pulumi_azure_native import applicationinsights
from pulumi_azure_native import authorization
from pulumi_azure_native import containerregistry
from pulumi_azure_native import network
from pulumi_azure_native import operationalinsights
from pulumi_azure_native import storage
from pulumi_azure_native import web
from pulumi_azure_native.resources import ResourceGroup
from pulumi_command import local as command

from ms.infra.core.settings import settings
from ms.infra.utils.docker import build_docker_image
from ms.infra.utils.docker import create_and_login_acr
from ms.infra.utils.easy_auth import configure_easy_auth
from ms.infra.utils.models.app_service_plan import AppServicePlanConfig
from ms.infra.utils.models.azure_function import AzureFunction
from ms.infra.utils.models.common_pulumi_config import COMMON_CONFIG
from ms.infra.utils.models.role_assignment_info import RoleAssignmentInfo
from ms.infra.utils.roles import BuiltInRole
from ms.infra.utils.storage import create_storage_account_for_durable_function
from ms.infra.utils.vnet import PrivateDnsZones
from ms.infra.utils.vnet import StorageSubResource
from ms.infra.utils.vnet import create_storage_private_endpoints


def create_app_service_plan(
    name: str,
    resource_group: ResourceGroup,
    config: AppServicePlanConfig,
) -> web.AppServicePlan:
    """
    Create an App Service Plan from the given configuration.

    Args:
        name: The name of the App Service Plan (the dictionary key from config).
        resource_group: The resource group where the plan will be created.
        config: The App Service Plan configuration (SKU, worker count).

    Returns:
        The created App Service Plan resource.
    """
    return web.AppServicePlan(
        f"asp-{name}",
        resource_group_name=resource_group.name,
        location=config.location,
        kind="FunctionApp" if config.is_elastic_premium else "linux",
        reserved=True,  # Indicates Linux
        maximum_elastic_worker_count=config.maximum_elastic_worker_count if config.is_elastic_premium else None,
        sku=web.SkuDescriptionArgs(
            name=config.sku_name,
            tier=config.sku_tier,
        ),
    )


def create_single_azure_function(
    function: AzureFunction,
    resource_group: ResourceGroup,
    plan: web.AppServicePlan,
    acr: containerregistry.Registry,
    acr_login: command.Command,
    env_vars: dict[str, str | pulumi.Output[Any]] | None = None,
    additional_role_assignments: list[RoleAssignmentInfo] | None = None,
    prev_deployment: web.WebApp | None = None,
    vnet_subnet_id: pulumi.Output[str] | None = None,
    private_endpoints_subnet: network.Subnet | None = None,
    private_dns_zones: PrivateDnsZones | None = None,
) -> web.WebApp:
    """
    Create a single Azure Function.

    Use this method when you need fine-grained control over Azure Function creation,
    such as:
    - Creating functions with inter-dependencies (control creation order)
    - Passing function-specific environment variables
    - Creating functions conditionally based on configuration
    - Integrating with other infrastructure resources that depend on specific functions

    For simple scenarios with independent functions that all receive the same env vars,
    use deploy_azure_functions() instead.

    Args:
        function: The Azure Function configuration
        resource_group: The resource group where the function will be created
        plan: The App Service Plan to use
        acr: The Azure Container Registry
        acr_login: The ACR login configuration
        env_vars: Additional environment variables for the function
        additional_role_assignments: Additional role assignments for the function's managed identity
        prev_deployment: Previous deployment to depend on (for sequential deployment)
        vnet_subnet_id: Subnet ID for VNet integration (delegated to Microsoft.Web/serverFarms)
        private_endpoints_subnet: Subnet for placing private endpoints (for durable storage)
        private_dns_zones: Private DNS zones for storage private endpoint DNS registration

    Returns:
        The created WebApp (Azure Function) resource
    """
    app_name = function.app_name

    durable_storage_account: storage.StorageAccount | None = None
    if function.is_durable:
        durable_storage_account = create_storage_account_for_durable_function(resource_group, app_name)

        if private_endpoints_subnet and private_dns_zones:
            create_storage_private_endpoints(
                resource_group=resource_group,
                storage_account=durable_storage_account,
                subnet=private_endpoints_subnet,
                dns_zones=private_dns_zones,
                sub_resources=list(StorageSubResource),
                name_prefix=f"{app_name}-durable",
                location=plan.location,
            )

    image = build_docker_image(
        acr=acr,
        acr_login=acr_login,
        app=function,
    )

    # App Insights for the Function app
    application_insights = applicationinsights.Component(
        f"{app_name}-appinsights",
        resource_group_name=resource_group.name,
        application_type=applicationinsights.ApplicationType.WEB,
        kind="web",
        ingestion_mode=applicationinsights.IngestionMode.LOG_ANALYTICS,
        workspace_resource_id=operationalinsights.Workspace(
            f"{app_name}-log-analytics",
            resource_group_name=resource_group.name,
            sku=operationalinsights.WorkspaceSkuArgs(
                name=operationalinsights.WorkspaceSkuNameEnum.PER_GB2018,
            ),
            retention_in_days=30,
        ).id,
    )

    # Environment variables for the Function app
    func_env_vars = {
        "BUILD_ID": settings.build_id,
        "FUNCTIONS_WORKER_RUNTIME": "python",
        "FUNCTIONS_EXTENSION_VERSION": "~4",
        "AzureWebJobsFeatureFlags": "EnableWorkerIndexing",
        "PYTHON_ENABLE_WORKER_INDEXING": "1",
        "WEBSITES_ENABLE_APP_SERVICE_STORAGE": "false",
        "DOCKER_CUSTOM_IMAGE_NAME": image.ref,
        # ACR auth settings
        "DOCKER_REGISTRY_SERVER_URL": pulumi.Output.concat("https://", acr.login_server),
        # App insights
        "APPLICATIONINSIGHTS_CONNECTION_STRING": pulumi.Output.secret(application_insights.connection_string),
        # Disable log sampling so we capture all logs
        "AzureFunctionsJobHost__Logging__ApplicationInsights__SamplingSettings__IsEnabled": "false",
        # Enable container console logging
        "AzureFunctionsJobHost__Logging__Console__IsEnabled": "true",
        # Custom environment variables from function config
        **(function.env or {}),
        # Additional env vars passed to the deploy function
        **(env_vars or {}),
    }

    # Identity-based storage auth for durable functions
    if durable_storage_account:
        func_env_vars["AzureWebJobsStorage__accountName"] = durable_storage_account.name
        func_env_vars["AzureWebJobsStorage__credential"] = "managedidentity"

    # VNet integration: route all traffic through VNet for private endpoint DNS resolution
    if vnet_subnet_id is not None:
        func_env_vars["WEBSITE_VNET_ROUTE_ALL"] = "1"
        # Azure's internal DNS resolver — required for private endpoint name resolution inside VNet
        func_env_vars["WEBSITE_DNS_SERVER"] = "168.63.129.16"
        # Pull container images over public network, not through VNet
        # (VNet has no NAT gateway / outbound internet route)
        func_env_vars["WEBSITE_PULL_IMAGE_OVER_VNET"] = "false"

    # Azure function, referencing docker image in ACR
    # Location must match the App Service Plan's region
    func = web.WebApp(
        f"fastapi-func-{app_name}",
        resource_group_name=resource_group.name,
        location=plan.location,
        server_farm_id=plan.id,
        kind="functionapp",
        identity=web.ManagedServiceIdentityArgs(type=web.ManagedServiceIdentityType.SYSTEM_ASSIGNED),
        virtual_network_subnet_id=vnet_subnet_id,
        site_config=web.SiteConfigArgs(
            linux_fx_version=pulumi.Output.concat("DOCKER|", image.ref),
            acr_use_managed_identity_creds=True,
            functions_runtime_scale_monitoring_enabled=function.runtime_scale_monitoring_enabled,
            vnet_route_all_enabled=vnet_subnet_id is not None,
            app_settings=[web.NameValuePairArgs(name=k, value=v) for k, v in func_env_vars.items()],
        ),
        https_only=True,
        opts=pulumi.ResourceOptions(
            depends_on=[image, prev_deployment] if prev_deployment else [image],
            custom_timeouts=pulumi.CustomTimeouts(create="30m", update="30m"),
        ),
    )

    # Role assignment: give the Function MI access to pull images from ACR
    authorization.RoleAssignment(
        f"acr-pull-{app_name}",
        principal_id=func.identity.principal_id,
        principal_type=authorization.PrincipalType.SERVICE_PRINCIPAL,
        role_definition_id=BuiltInRole.ACR_PULL.to_definition_id(),
        scope=acr.id,
        opts=pulumi.ResourceOptions(depends_on=[func]),
    )

    # Role assignments: give the Function MI access to durable function storage
    if durable_storage_account:
        for role_name, role in [
            ("blob", BuiltInRole.STORAGE_BLOB_DATA_CONTRIBUTOR),
            ("queue", BuiltInRole.STORAGE_QUEUE_DATA_CONTRIBUTOR),
            ("table", BuiltInRole.STORAGE_TABLE_DATA_CONTRIBUTOR),
        ]:
            authorization.RoleAssignment(
                f"ra-{app_name}-storage-{role_name}",
                principal_id=func.identity.principal_id,
                principal_type=authorization.PrincipalType.SERVICE_PRINCIPAL,
                role_definition_id=role.to_definition_id(),
                scope=durable_storage_account.id,
                opts=pulumi.ResourceOptions(depends_on=[func]),
            )

    # Easy Auth Configuration:
    # Get Easy Auth config mappings from stack config
    easy_auth_config = COMMON_CONFIG.easy_auth_configs.get(app_name)
    if not easy_auth_config:
        # Absence of Easy Auth only allowed in dev stacks for testing
        assert settings.is_dev_stack, (
            f"An Easy Auth Client ID is required for Azure Function '{app_name}' in stack '{settings.stack_name}'."
        )
    else:
        configure_easy_auth(
            function_app=func,
            resource_group_name=resource_group.name,
            app_name=app_name,
            easy_auth_config=easy_auth_config,
        )

    # Give the Function MI any additional roles to other resources as specified
    if additional_role_assignments:
        for ra in additional_role_assignments:
            ra.create_service_principal_role_assignment(
                principal_id=func.identity.principal_id,
                prefix=app_name,
            )

    pulumi.export(app_name, func.default_host_name.apply(lambda hostname: f"https://{hostname}" if hostname else ""))

    return func


def deploy_azure_functions(
    resource_group: ResourceGroup,
    env_vars: dict[str, str | pulumi.Output[Any]] | None = None,
    additional_role_assignments: list[RoleAssignmentInfo] | None = None,
    acr: containerregistry.Registry | None = None,
    acr_login: command.Command | None = None,
    vnet_subnet_id: pulumi.Output[str] | None = None,
    private_endpoints_subnet: network.Subnet | None = None,
    private_dns_zones: PrivateDnsZones | None = None,
) -> dict[str, web.WebApp]:
    """
    Create multiple Azure Functions based on configuration.

    Use this method when there are no inter-function dependencies and all functions
    can receive the same dynamic environment variables. For scenarios with
    dependencies between functions or function-specific env vars, use create_single_azure_function
    to control creation order and pass different env vars per function.

    Args:
        resource_group: The resource group where functions will be created
        env_vars: Dynamic environment variables to apply to all functions
        additional_role_assignments: Additional role assignments for all functions' managed identities
        acr: Optional shared ACR. If not provided, one is created internally.
        acr_login: Optional shared ACR login command. Required if acr is provided.
        vnet_subnet_id: Subnet ID for VNet integration (delegated to Microsoft.Web/serverFarms)
        private_endpoints_subnet: Subnet for placing private endpoints (for durable storage)
        private_dns_zones: Private DNS zones for storage private endpoint DNS registration

    Returns:
        Dictionary mapping function names to their WebApp resources
    """
    functions = COMMON_CONFIG.functions

    # Skip execution if no functions are defined in config
    if not functions:
        return {}

    # Create all App Service Plans
    assert COMMON_CONFIG.app_service_plans, (
        "app_service_plans must be configured when functions are defined. "
        "Add app_service_plans to your Pulumi config YAML."
    )
    plans: dict[str, web.AppServicePlan] = {
        name: create_app_service_plan(name=name, resource_group=resource_group, config=config)
        for name, config in COMMON_CONFIG.app_service_plans.items()
    }

    function_map: dict[str, web.WebApp] = {}
    if acr is None or acr_login is None:
        acr, acr_login = create_and_login_acr(resource_group=resource_group)

    # Deploy sequentially — parallel deployment to the same service plan can fail.
    prev_deployment = None

    # Create Azure Functions for each app
    for app_name, function in functions.items():
        if function.plan not in plans:
            raise ValueError(
                f"Function '{app_name}' references plan '{function.plan}' "
                f"but available plans are: {sorted(plans.keys())}"
            )

        func = create_single_azure_function(
            function=function,
            resource_group=resource_group,
            plan=plans[function.plan],
            acr=acr,
            acr_login=acr_login,
            env_vars=env_vars,
            additional_role_assignments=additional_role_assignments,
            prev_deployment=prev_deployment,
            vnet_subnet_id=vnet_subnet_id,
            private_endpoints_subnet=private_endpoints_subnet,
            private_dns_zones=private_dns_zones,
        )

        prev_deployment = func
        function_map[app_name] = func

    return function_map
