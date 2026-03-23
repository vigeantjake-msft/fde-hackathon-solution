import pulumi
from pulumi import ComponentResource
from pulumi import Output
from pulumi import ResourceOptions
from pulumi_azure_native import cognitiveservices
from pulumi_random import RandomString

from ms.infra.core.naming import sanitize_for_resource_name

_MAX_NAME_LENGTH = 64
_SUFFIX_LENGTH = 6


class FoundryAccount(ComponentResource):
    """Wrapper for Azure AI Foundry Account (Cognitive Services account kind=AIServices).

    This component provisions an AIServices account with allowProjectManagement enabled,
    which is required for Foundry projects. Uses the typed cognitiveservices.Account
    resource — the allowProjectManagement property was added in pulumi-azure-native v3.14.0.

    See: https://github.com/pulumi/pulumi-azure-native/issues/4354
    """

    account_name: Output[str]
    account_id: Output[str]
    endpoint: Output[str]
    account: cognitiveservices.Account

    def __init__(
        self,
        name: str,
        *,
        resource_group_name: pulumi.Input[str],
        location: pulumi.Input[str],
        default_project_name: pulumi.Input[str],
        account_name: pulumi.Output[str | None] | str | None = None,
        sku_name: str = "S0",
        allow_project_management: bool = True,
        public_network_access: bool = True,
        custom_subdomain_name: pulumi.Output[str | None] | str | None = None,
        opts: ResourceOptions | None = None,
    ) -> None:
        super().__init__(
            "custom:foundry:FoundryAccount",
            name=name,
            props=None,
            opts=opts,
        )

        # Always create the RandomString so it's available as a fallback when
        # account_name is an Output that resolves to None at runtime (e.g. the
        # legacy lookup in deploy_foundry_with_project).
        suffix = RandomString(
            f"{name}-random-suffix",
            length=_SUFFIX_LENGTH,
            special=False,
            upper=False,
            opts=ResourceOptions(parent=self),
        )
        sanitized_base = sanitize_for_resource_name(name).lower()
        truncated_base = sanitized_base[: _MAX_NAME_LENGTH - _SUFFIX_LENGTH].rstrip("-")
        generated_name = Output.concat(truncated_base, suffix.result)

        if account_name is None:
            resolved_name: pulumi.Input[str] = generated_name
        else:
            # account_name may be Output[str | None] — use the provided value when
            # non-None, otherwise fall back to the generated name with random suffix.
            # NOTE: We use a nested .apply() instead of Output.all() to avoid marking
            # the result as unknown during preview. Output.all() would collect
            # generated_name (unknown for new RandomString resources) as a dependency,
            # causing the entire result to be unknown even when the provided name is
            # known. Returning an Output from .apply() is auto-flattened by Pulumi.
            resolved_name = Output.from_input(account_name).apply(lambda n: n if n is not None else generated_name)

        if custom_subdomain_name is None:
            subdomain: pulumi.Input[str] = resolved_name
        else:
            # custom_subdomain_name may be an Output that resolves to None at runtime
            # (e.g. legacy name for existing accounts, None for new accounts).
            # Fall back to resolved_name when the Output resolves to None.
            # Uses nested .apply() instead of Output.all() to avoid unknown propagation
            # (see resolved_name comment above).
            subdomain = Output.from_input(custom_subdomain_name).apply(lambda n: n if n is not None else resolved_name)
        public_network_access_str = "Enabled" if public_network_access else "Disabled"

        account = cognitiveservices.Account(
            f"{name}-account",
            account_name=resolved_name,
            resource_group_name=resource_group_name,
            location=location,
            kind="AIServices",
            identity=cognitiveservices.IdentityArgs(type=cognitiveservices.ResourceIdentityType.SYSTEM_ASSIGNED),
            sku=cognitiveservices.SkuArgs(name=sku_name),
            properties=cognitiveservices.AccountPropertiesArgs(
                api_properties=cognitiveservices.ApiPropertiesArgs(),
                custom_sub_domain_name=subdomain,
                network_acls=cognitiveservices.NetworkRuleSetArgs(
                    default_action=cognitiveservices.NetworkRuleAction.ALLOW,
                    virtual_network_rules=[],
                    ip_rules=[],
                ),
                allow_project_management=allow_project_management,
                default_project=default_project_name,
                associated_projects=[default_project_name],
                public_network_access=public_network_access_str,
            ),
            opts=ResourceOptions(
                parent=self,
                # Alias the old URN so existing stacks that provisioned this resource
                # via the generic resources resource (Pulumi type azure-native:resources:Resource)
                # see an in-place update instead of a destructive delete+create.
                aliases=[pulumi.Alias(type_="azure-native:resources:Resource")],
            ),
        )

        self.account = account
        self.account_name = account.name
        self.account_id = account.id
        self.endpoint = Output.concat("https://", subdomain, ".cognitiveservices.azure.com/")

        self.register_outputs(
            {
                "account_name": self.account_name,
                "account_id": self.account_id,
                "endpoint": self.endpoint,
            }
        )
