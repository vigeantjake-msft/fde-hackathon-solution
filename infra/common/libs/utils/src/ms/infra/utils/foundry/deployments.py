import pulumi
import pulumi_azuread as azuread
from pulumi import CustomTimeouts
from pulumi import ResourceOptions
from pulumi_azure_native import authorization
from pulumi_azure_native import cognitiveservices
from pulumi_azure_native import config
from pulumi_azure_native.resources import ResourceGroup
from typing_extensions import deprecated

from ms.infra.core.settings import settings
from ms.infra.utils.foundry.resources import FoundryAccount
from ms.infra.utils.models.azure_openai_model import AzureOpenAiModel
from ms.infra.utils.models.common_pulumi_config import COMMON_CONFIG
from ms.infra.utils.roles import BuiltInRole


def _deploy_model_deployments(
    account_name: pulumi.Input[str],
    resource_group_name: pulumi.Input[str],
    models: list[AzureOpenAiModel],
    depends_on: list[pulumi.Resource] | None = None,
) -> None:
    """Deploy OpenAI models to a Foundry/Cognitive Services account.
    Models are deployed sequentially to avoid concurrent provisioning failures.
    """
    prev_deployment = None
    for model in models:
        # First deployment depends on the account; subsequent deployments chain off previous
        deps = depends_on if prev_deployment is None else [prev_deployment]
        curr_deployment = cognitiveservices.Deployment(
            model.deployment_name,
            account_name=account_name,
            resource_group_name=resource_group_name,
            deployment_name=model.deployment_name,
            sku=cognitiveservices.SkuArgs(
                name=model.sku_name,
                capacity=model.capacity,
            ),
            properties=cognitiveservices.DeploymentPropertiesArgs(
                model=cognitiveservices.DeploymentModelArgs(
                    format="OpenAI",  # For Azure OpenAI models
                    name=model.model_name,
                    version=model.version,
                ),
                rai_policy_name=model.rai_policy_name,
                version_upgrade_option=model.version_upgrade_option,
            ),
            opts=ResourceOptions(
                depends_on=deps,
                custom_timeouts=CustomTimeouts(create="30m", update="30m"),
            ),
        )

        # Chain dependencies to avoid concurrent model provisioning (leads to failures)
        prev_deployment = curr_deployment


def _assign_github_actions_foundry_role(
    scope: pulumi.Input[str],
    role: BuiltInRole = BuiltInRole.COGNITIVE_SERVICES_OPENAI_USER,
) -> None:
    """Assign GitHub Actions service principal access to a Foundry resource.
    Only applies in staging stacks. No-op in other environments.
    """
    if not settings.is_staging_stack:
        return

    github_actions_sp = azuread.get_service_principal(
        client_id=settings.client_id,
    )
    authorization.RoleAssignment(
        "ra-github-actions-foundry",
        role_definition_id=role.to_definition_id(),
        principal_id=github_actions_sp.object_id,
        principal_type=authorization.PrincipalType.SERVICE_PRINCIPAL,
        scope=scope,
    )


def _resolve_existing_account_name(old_name: str, resource_group_name: str) -> str | None:
    """Look up whether a Foundry account with the legacy naming convention already exists.

    Returns the old account name if found (preserving the existing Azure resource),
    or None if not found (allowing Pulumi to auto-generate a new name).

    Any exception from the Pulumi invoke is treated as "not found" because Pulumi's
    invoke mechanism does not expose a distinct HTTP-404 error type; all failures
    (resource missing, transient network issues, etc.) surface as generic exceptions.
    A warning is logged so unexpected failures remain visible in deployment logs.
    """
    try:
        cognitiveservices.get_account(
            account_name=old_name,
            resource_group_name=resource_group_name,
        )
        return old_name
    except Exception as exc:
        pulumi.warn(
            f"Lookup for Foundry account with legacy name '{old_name}' in resource group "
            f"'{resource_group_name}' failed (treating as not found). This may indicate that the account "
            f"does not exist, or it may be due to transient/network/auth issues. Pulumi may create or use a "
            f"new account with a generated name if one is not already present. Underlying error: {exc}"
        )
        return None


@deprecated("Use deploy_foundry_with_project() instead.")
def deploy_foundry_resources(resource_group: ResourceGroup) -> cognitiveservices.Account:
    """Deploy Azure AI Foundry resources using the standard Cognitive Services Account.

    This function creates a Cognitive Services Account (kind 'AIServices') without
    project management enabled. Use deploy_foundry_with_project() for the newer
    project-based Foundry model.

    Note: Mutually exclusive with deploy_foundry_with_project().
    """
    # AI Foundry resource = Cognitive Services Account (kind 'AIServices')
    acct = cognitiveservices.Account(
        "foundry",
        resource_group_name=resource_group.name,
        location=config.location,
        kind="AIServices",
        sku=cognitiveservices.SkuArgs(name="S0"),
        properties=cognitiveservices.AccountPropertiesArgs(
            public_network_access="Enabled",  # or "Disabled" + networkAcls, etc.
            # This is required in order to authenticate to the endpoints under this
            # account via managed identities. It also needs to be globally unique, so
            # including both the project name and the stack name (dev-<name>/staging/production).
            # https://learn.microsoft.com/en-us/azure/ai-services/cognitive-services-custom-subdomains
            custom_sub_domain_name=f"{settings.project_name}-{settings.stack_name}",
        ),
        identity=cognitiveservices.IdentityArgs(type=cognitiveservices.ResourceIdentityType.SYSTEM_ASSIGNED),
    )

    # In staging, give the GitHub Actions OIDC client access to the Foundry account
    # so that we can use it to run prompt evals.
    _assign_github_actions_foundry_role(acct.id)

    # Foundry model deployments under the Account
    models = COMMON_CONFIG.openai_models or []
    _deploy_model_deployments(acct.name, resource_group.name, models)

    # Output so Azure Function deployment has these values
    return acct


def deploy_foundry_with_project(
    resource_group: ResourceGroup,
) -> tuple[FoundryAccount, cognitiveservices.Project]:
    """Deploy a Foundry account with project management and a default project.

    This function creates:
    1. A FoundryAccount with allowProjectManagement enabled
    2. A Project under that account
    3. Model deployments (from config)
    4. GitHub Actions IAM (in staging)

    For existing stacks the legacy account name (``{project}-{stack}``) is preserved via
    a ``getAccount`` look-up; brand-new stacks receive a Pulumi-generated name instead.

    Note: Mutually exclusive with deploy_foundry_resources().
    """
    legacy_name = f"{settings.project_name}-{settings.stack_name}".lower()

    # Check whether the legacy-named account already exists in the resource group.
    # When the resource group name Output resolves, _resolve_existing_account_name is called.
    # Returns the legacy name if found (backward compat), or None for a new deployment
    # so Pulumi can auto-generate the Azure resource name.
    account_name = resource_group.name.apply(lambda rg_name: _resolve_existing_account_name(legacy_name, rg_name))

    # For existing accounts, preserve legacy names to avoid resource recreation.
    # For new accounts, use clean names (FoundryAccount generates globally-unique defaults).
    project_name: pulumi.Output[str] = account_name.apply(lambda n: legacy_name if n is not None else "default")
    custom_subdomain_name: pulumi.Output[str | None] = account_name.apply(
        lambda n: legacy_name if n is not None else None
    )

    # Create the Foundry account with project management enabled
    foundry_account = FoundryAccount(
        "foundry",
        resource_group_name=resource_group.name,
        location=resource_group.location,
        account_name=account_name,
        custom_subdomain_name=custom_subdomain_name,
        default_project_name=project_name,
    )

    # Create the default project (depends on account being fully created)
    # Use parent= for deletion order and depends_on= for creation order
    foundry_project = cognitiveservices.Project(
        "project",
        resource_group_name=resource_group.name,
        account_name=foundry_account.account_name,
        project_name=project_name,
        location=resource_group.location,
        identity=cognitiveservices.IdentityArgs(
            type=cognitiveservices.ResourceIdentityType.SYSTEM_ASSIGNED,
        ),
        properties=cognitiveservices.ProjectPropertiesArgs(
            description="Default Foundry project (Microsoft-managed backing resources)",
            display_name=project_name,
        ),
        opts=ResourceOptions(
            parent=foundry_account,
            depends_on=[foundry_account.account],
            # Alias the old URN (before parent was added) so Pulumi doesn't
            # delete+recreate the project due to the URN change.
            aliases=[pulumi.Alias(parent=pulumi.ROOT_STACK_RESOURCE)],
        ),
    )

    # In staging, give the GitHub Actions OIDC client access
    _assign_github_actions_foundry_role(foundry_account.account_id)

    # Deploy models from config (depends on foundry_account being fully created)
    models = COMMON_CONFIG.openai_models or []
    _deploy_model_deployments(
        foundry_account.account_name,
        resource_group.name,
        models,
        depends_on=[foundry_account.account],
    )

    return foundry_account, foundry_project
