"""Utilities for configuring Azure Easy Authentication with Entra ID."""

import pulumi
import pulumi_azuread as azuread
from pulumi_azure_native import app
from pulumi_azure_native import web

from ms.infra.core.settings import settings
from ms.infra.utils.models.easy_auth_config import EasyAuthConfig


def get_or_create_app_registration(
    app_name: str,
    easy_auth_app_client_id: str | None,
    app_url: pulumi.Output[str],
) -> pulumi.Output[str]:
    """
    Get or create an Entra ID application registration for Easy Auth.

    Since the GitHub Action service principal might not have privileges to create apps,
    this function supports both scenarios:
    1. Use a pre-existing app registration (if app_client_id is provided)
    2. Create a new app registration (if permissions allow)

    Args:
        app_name: Name of the Azure app (Function App or Container App)
        easy_auth_app_client_id: Easy Auth application client ID
        app_url: URL of the app

    Returns:
        client_id
    """
    if easy_auth_app_client_id:
        # Use pre-existing app registration
        # Note: We can't modify the app registration due to limited permissions,
        # so redirect URIs must be configured manually by someone with privileges
        return pulumi.Output.from_input(easy_auth_app_client_id)

    # Default redirect URI for Easy Auth
    default_redirect_uri = app_url.apply(lambda url: f"{url}/.auth/login/aad/callback")

    application = azuread.Application(
        f"{app_name}-easyauth-app",
        display_name=f"{app_name}-easyauth",
        sign_in_audience="AzureADMyOrg",  # Single tenant
        web=azuread.ApplicationWebArgs(
            redirect_uris=[default_redirect_uri],
            implicit_grant=azuread.ApplicationWebImplicitGrantArgs(
                access_token_issuance_enabled=True,
                id_token_issuance_enabled=True,
            ),
        ),
        # Required API permissions for Easy Auth
        required_resource_accesses=[
            azuread.ApplicationRequiredResourceAccessArgs(
                resource_app_id="00000003-0000-0000-c000-000000000000",  # Microsoft Graph
                resource_accesses=[
                    azuread.ApplicationRequiredResourceAccessResourceAccessArgs(
                        id="e1fe6dd8-ba31-4d61-89e7-88639da4683d",  # User.Read
                        type="Scope",
                    ),
                ],
            ),
        ],
    )

    return application.client_id


def configure_easy_auth(
    function_app: web.WebApp,
    resource_group_name: pulumi.Input[str],
    app_name: str,
    easy_auth_config: EasyAuthConfig,
) -> web.WebAppAuthSettingsV2:
    """
    Configure Easy Authentication for an Azure Function App.

    Args:
        function_app: The Azure Function App resource
        resource_group_name: Name of the resource group
        app_name: Name of the function app
        easy_auth_config: Easy Auth configuration

    Returns:
        WebAppAuthSettingsV2 resource
    """
    function_url = function_app.default_host_name.apply(lambda hostname: f"https://{hostname}")
    client_id = get_or_create_app_registration(
        app_name=app_name,
        easy_auth_app_client_id=easy_auth_config.easy_auth_app_client_id,
        app_url=function_url,
    )

    auth = web.WebAppAuthSettingsV2(
        f"{app_name}-auth-settings",
        name=function_app.name,
        resource_group_name=resource_group_name,
        global_validation=web.GlobalValidationArgs(
            unauthenticated_client_action=web.UnauthenticatedClientActionV2.REDIRECT_TO_LOGIN_PAGE,
            require_authentication=True,
        ),
        identity_providers=web.IdentityProvidersArgs(
            azure_active_directory=web.AzureActiveDirectoryArgs(
                enabled=True,
                registration=web.AzureActiveDirectoryRegistrationArgs(
                    client_id=client_id,
                    # Issuer for single-tenant: https://login.microsoftonline.com/<tenantId>/v2.0
                    # Easy Auth compares the incoming token’s iss to this value and rejects mismatches at the gateway
                    open_id_issuer=pulumi.Output.concat(
                        "https://login.microsoftonline.com/", settings.tenant_id, "/v2.0"
                    ),
                ),
                # Client application requirement: whitelist caller apps, both in policy and JWT claims required
                validation=web.AzureActiveDirectoryValidationArgs(
                    allowed_audiences=[client_id],
                    default_authorization_policy=web.DefaultAuthorizationPolicyArgs(
                        allowed_applications=easy_auth_config.allowed_app_client_ids,
                    ),
                    jwt_claim_checks=web.JwtClaimChecksArgs(
                        allowed_client_applications=easy_auth_config.allowed_app_client_ids,
                    ),
                ),
            ),
        ),
        login=web.LoginArgs(token_store=web.TokenStoreArgs(enabled=True)),
        platform=web.AuthPlatformArgs(enabled=True),
    )

    return auth


def configure_container_app_easy_auth(
    container_app: app.ContainerApp,
    resource_group_name: pulumi.Input[str],
    app_name: str,
    easy_auth_config: EasyAuthConfig,
) -> app.ContainerAppsAuthConfig:
    """
    Configure Easy Authentication for an Azure Container App.

    Args:
        container_app: The Azure Container App resource
        resource_group_name: Name of the resource group
        app_name: Name of the container app
        easy_auth_config: Easy Auth configuration

    Returns:
        ContainerAppsAuthConfig resource
    """
    if not settings.is_dev_stack:
        assert easy_auth_config.easy_auth_app_client_id, (
            f"easy_auth_app_client_id is required for Container App '{app_name}' "
            f"in stack '{settings.stack_name}'. Auto-creation requires Application.ReadWrite.All "
            f"which the CI service principal may not have."
        )

    container_app_url = container_app.configuration.apply(
        lambda config: f"https://{config.ingress.fqdn}" if config and config.ingress else ""
    )
    client_id = get_or_create_app_registration(
        app_name=app_name,
        easy_auth_app_client_id=easy_auth_config.easy_auth_app_client_id,
        app_url=container_app_url,
    )

    auth = app.ContainerAppsAuthConfig(
        f"{app_name}-auth-settings",
        auth_config_name="current",
        container_app_name=container_app.name,
        resource_group_name=resource_group_name,
        global_validation=app.GlobalValidationArgs(
            unauthenticated_client_action=app.UnauthenticatedClientActionV2.RETURN401,
        ),
        identity_providers=app.IdentityProvidersArgs(
            azure_active_directory=app.AzureActiveDirectoryArgs(
                enabled=True,
                registration=app.AzureActiveDirectoryRegistrationArgs(
                    client_id=client_id,
                    open_id_issuer=pulumi.Output.concat(
                        "https://login.microsoftonline.com/", settings.tenant_id, "/v2.0"
                    ),
                ),
                validation=app.AzureActiveDirectoryValidationArgs(
                    allowed_audiences=[client_id],
                    default_authorization_policy=app.DefaultAuthorizationPolicyArgs(
                        allowed_applications=easy_auth_config.allowed_app_client_ids,
                    ),
                    jwt_claim_checks=app.JwtClaimChecksArgs(
                        allowed_client_applications=easy_auth_config.allowed_app_client_ids,
                    ),
                ),
            ),
        ),
        login=app.LoginArgs(token_store=app.TokenStoreArgs(enabled=True)),
        platform=app.AuthPlatformArgs(enabled=True),
    )

    return auth
