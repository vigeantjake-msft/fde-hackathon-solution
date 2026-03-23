from typing import Any

import pulumi
from pulumi_azure_native import app
from pulumi_azure_native import containerregistry
from pulumi_azure_native import managedidentity
from pulumi_azure_native import operationalinsights
from pulumi_azure_native import resources
from pulumi_command import local as command

from ms.infra.core.settings import settings
from ms.infra.utils.docker import build_docker_image
from ms.infra.utils.docker import create_and_login_acr
from ms.infra.utils.easy_auth import configure_container_app_easy_auth
from ms.infra.utils.models.common_pulumi_config import COMMON_CONFIG
from ms.infra.utils.models.container_app import ContainerApp
from ms.infra.utils.models.role_assignment_info import RoleAssignmentInfo
from ms.infra.utils.roles import BuiltInRole


def create_single_container_app(
    container_app: ContainerApp,
    resource_group: resources.ResourceGroup,
    container_apps_environment: app.ManagedEnvironment,
    acr: containerregistry.Registry,
    acr_login: command.Command,
    env_vars: dict[str, str | pulumi.Output[Any]] | None = None,
    additional_role_assignments: list[RoleAssignmentInfo] | None = None,
    additional_build_args: dict[str, str | pulumi.Output[Any]] | None = None,
) -> app.ContainerApp:
    """
    Create a single container app.

    Use this method when you need fine-grained control over container app creation,
    such as:
    - Creating apps with inter-dependencies (control creation order)
    - Passing app-specific environment variables
    - Creating apps conditionally based on configuration
    - Integrating with other infrastructure resources that depend on specific apps

    For simple scenarios with independent apps that all receive the same env vars,
    use create_container_apps() instead.

    Args:
        container_app: The container app configuration
        resource_group: The resource group where the app will be created
        container_apps_environment: The container apps environment to use
        acr: The Azure Container Registry
        acr_login: The ACR login configuration
        env_vars: Additional environment variables for the container app
        additional_role_assignments: Additional role assignments for the container app's managed identity
        additional_build_args: Additional build arguments for the Docker image

    Returns:
        The created ContainerApp resource
    """
    image = build_docker_image(
        acr=acr,
        acr_login=acr_login,
        app=container_app,
        additional_build_args=additional_build_args,
    )

    # Environment variables for the Container app
    container_env_vars: dict[str, str | pulumi.Output[Any]] = {
        "BUILD_ID": settings.build_id,
        # Custom environment variables from app config
        **(container_app.env or {}),
        # Additional env vars passed to the container app
        **(env_vars or {}),
    }

    # Create a user-assigned MI for ACR image pulls.
    # Must exist before the container app so the role is in place for the first image pull.
    acr_pull_identity = managedidentity.UserAssignedIdentity(
        f"{container_app.app_name}-acr-pull-identity",
        resource_group_name=resource_group.name,
    )
    acr_pull_role = RoleAssignmentInfo(
        name="acr-pull",
        role=BuiltInRole.ACR_PULL,
        scope=acr.id,
    ).create_service_principal_role_assignment(
        principal_id=acr_pull_identity.principal_id,
        prefix=container_app.app_name,
    )

    created_container_app = app.ContainerApp(
        container_app.app_name,
        resource_group_name=resource_group.name,
        managed_environment_id=container_apps_environment.id,
        identity=app.ManagedServiceIdentityArgs(
            type=app.ManagedServiceIdentityType.SYSTEM_ASSIGNED_USER_ASSIGNED,
            user_assigned_identities=[acr_pull_identity.id],
        ),
        configuration=app.ConfigurationArgs(
            registries=[
                app.RegistryCredentialsArgs(
                    server=acr.login_server,
                    identity=acr_pull_identity.id,
                ),
            ],
            ingress=app.IngressArgs(
                external=container_app.ingress_transport_external,
                target_port=container_app.ingress_target_port,
                allow_insecure=False,
                traffic=[
                    app.TrafficWeightArgs(
                        weight=100,
                        latest_revision=True,
                    ),
                ],
            ),
        ),
        template=app.TemplateArgs(
            containers=[
                app.ContainerArgs(
                    name=container_app.app_name,
                    image=image.ref,
                    resources=app.ContainerResourcesArgs(
                        cpu=container_app.cpu,
                        memory=f"{container_app.memory_in_gb}Gi",
                    ),
                    env=[app.EnvironmentVarArgs(name=k, value=v) for k, v in container_env_vars.items()],
                ),
            ],
            scale=app.ScaleArgs(
                min_replicas=container_app.replicas_min,
                max_replicas=container_app.replicas_max,
                rules=[
                    app.ScaleRuleArgs(
                        name="http-rule",
                        http=app.HttpScaleRuleArgs(
                            metadata={"concurrentRequests": str(container_app.concurrent_requests_per_replica)},
                        ),
                    ),
                ],
            ),
        ),
        opts=pulumi.ResourceOptions(depends_on=[acr_pull_role]),
    )

    # Give the Container App MI any additional roles to other resources as specified
    if additional_role_assignments:
        for ra in additional_role_assignments:
            ra.create_service_principal_role_assignment(
                principal_id=created_container_app.identity.principal_id,
                prefix=container_app.app_name,
            )

    pulumi.export(
        container_app.app_name,
        pulumi.Output.unsecret(
            created_container_app.configuration.apply(
                lambda config: f"https://{config.ingress.fqdn}" if config and config.ingress else ""
            )
        ),
    )

    easy_auth_config = COMMON_CONFIG.easy_auth_configs.get(container_app.app_name)
    if easy_auth_config:
        configure_container_app_easy_auth(
            container_app=created_container_app,
            resource_group_name=resource_group.name,
            app_name=container_app.app_name,
            easy_auth_config=easy_auth_config,
        )

    return created_container_app


def create_container_apps(
    resource_group: resources.ResourceGroup,
    env_vars: dict[str, str | pulumi.Output[Any]] | None = None,
    additional_role_assignments: list[RoleAssignmentInfo] | None = None,
    additional_build_args: dict[str, str | pulumi.Output[Any]] | None = None,
    acr: containerregistry.Registry | None = None,
    acr_login: command.Command | None = None,
    container_apps_environment: app.ManagedEnvironment | None = None,
    log_analytics_workspace: operationalinsights.Workspace | None = None,
) -> dict[str, app.ContainerApp]:
    """
    Create multiple container apps based on configuration.

    Use this method when there are no inter-app dependencies and all apps
    can receive the same dynamic environment variables. For scenarios with
    dependencies between apps or app-specific env vars, use create_single_container_app
    to control creation order and pass different env vars per app.

    Args:
        resource_group: The resource group where container apps will be created
        env_vars: Dynamic environment variables to apply to all container apps
        additional_role_assignments: Additional role assignments for all container apps' managed identities
        additional_build_args: Additional build arguments for all container apps' Docker images
        acr: Optional shared ACR. If not provided, one is created internally.
        acr_login: Optional shared ACR login command. Required if acr is provided.
        container_apps_environment: Optional shared ManagedEnvironment. If not provided, one is created internally.
        log_analytics_workspace: Optional shared Log Analytics workspace. Must be in the same
            resource group as ``resource_group``. If not provided and no container_apps_environment
            is given, one is created internally. Useful when callers need to create Application
            Insights backed by the same workspace.

    Returns:
        Dictionary mapping container app names to their ContainerApp resources.
    """

    container_apps = COMMON_CONFIG.container_apps

    if not container_apps:
        return {}

    container_app_map: dict[str, app.ContainerApp] = {}
    if container_apps_environment is None:
        if log_analytics_workspace is None:
            log_analytics_workspace = operationalinsights.Workspace(
                "container-apps-log-analytics",
                resource_group_name=resource_group.name,
                retention_in_days=30,
                sku=operationalinsights.WorkspaceSkuArgs(
                    name=operationalinsights.WorkspaceSkuNameEnum.PER_GB2018,
                ),
            )
        log_analytics_keys = operationalinsights.get_shared_keys_output(
            resource_group_name=resource_group.name,
            workspace_name=log_analytics_workspace.name,
        )
        container_apps_environment = app.ManagedEnvironment(
            "container-apps-env",
            resource_group_name=resource_group.name,
            app_logs_configuration=app.AppLogsConfigurationArgs(
                destination="log-analytics",
                log_analytics_configuration=app.LogAnalyticsConfigurationArgs(
                    customer_id=log_analytics_workspace.customer_id,
                    shared_key=log_analytics_keys.primary_shared_key,
                ),
            ),
            opts=pulumi.ResourceOptions(custom_timeouts=pulumi.CustomTimeouts(create="15m")),
        )
    if acr is None or acr_login is None:
        acr, acr_login = create_and_login_acr(resource_group=resource_group)

    for app_name, container_app in container_apps.items():
        created_container_app = create_single_container_app(
            container_app=container_app,
            resource_group=resource_group,
            container_apps_environment=container_apps_environment,
            acr=acr,
            acr_login=acr_login,
            env_vars=env_vars,
            additional_role_assignments=additional_role_assignments,
            additional_build_args=additional_build_args,
        )

        container_app_map[app_name] = created_container_app

    return container_app_map
