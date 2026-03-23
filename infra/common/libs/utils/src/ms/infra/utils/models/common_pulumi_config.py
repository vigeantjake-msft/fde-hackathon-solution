from typing import Any
from typing import Self

import pulumi
from pydantic import Field
from pydantic import model_validator

from ms.infra.core.models.base import FrozenBaseModel
from ms.infra.utils.models.app_service_plan import AppServicePlanConfig
from ms.infra.utils.models.azure_function import AzureFunction
from ms.infra.utils.models.azure_openai_model import AzureOpenAiModel
from ms.infra.utils.models.container_app import ContainerApp
from ms.infra.utils.models.easy_auth_config import EasyAuthConfig


class CommonPulumiConfig(FrozenBaseModel):
    openai_models: list[AzureOpenAiModel] | None = Field(
        default=None,
        description="List of Azure OpenAI models to deploy.",
    )

    container_apps: dict[str, ContainerApp] | None = Field(
        default=None,
        description="Dictionary of app name to Azure Container App to deploy.",
    )

    functions: dict[str, AzureFunction] | None = Field(
        default=None,
        description="Dictionary of app name to Azure Function to deploy.",
    )

    app_service_plans: dict[str, AppServicePlanConfig] | None = Field(
        default=None,
        description="Dictionary of plan name to App Service Plan configuration, "
        "parsed directly from the Pulumi config YAML. "
        "Functions reference these by key via their 'plan' field.",
    )

    easy_auth_configs: dict[str, EasyAuthConfig] = Field(
        default_factory=dict,
        description="Mapping of Azure app names to their Easy Auth configurations.",
    )

    @model_validator(mode="after")
    def _validate_app_service_plan_locations(self) -> Self:
        """All App Service Plans must share the same location for VNet integration."""
        if not self.app_service_plans:
            return self
        plan_locations = {p.location for p in self.app_service_plans.values() if p.location}
        if len(plan_locations) > 1:
            msg = f"All App Service Plans must share the same location for VNet integration, got: {plan_locations}"
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def _validate_runtime_scale_monitoring(self) -> Self:
        """Reject runtime_scale_monitoring_enabled on non-ElasticPremium plans."""
        if not self.functions or not self.app_service_plans:
            return self
        for name, function in self.functions.items():
            if not function.runtime_scale_monitoring_enabled:
                continue
            plan_config = self.app_service_plans.get(function.plan)
            if plan_config and not plan_config.is_elastic_premium:
                raise ValueError(
                    f"Function '{name}' has runtime_scale_monitoring_enabled=True, "
                    f"but plan '{function.plan}' has sku_tier='{plan_config.sku_tier}'. "
                    f"Runtime scale monitoring is only supported on ElasticPremium plans. "
                    f"Set runtime_scale_monitoring_enabled=False for this function."
                )
        return self

    @classmethod
    def from_pulumi_config(cls) -> Self:
        p_config = pulumi.Config()

        # Transform container_apps from list to dict keyed by app name
        container_apps_list: list[dict[Any, Any]] = p_config.get_object("container_apps") or []
        container_apps_dict = (
            {app["app_name"]: ContainerApp.model_validate(app) for app in container_apps_list}
            if container_apps_list
            else None
        )

        # Transform functions from list to dict keyed by function name
        functions_list: list[dict[Any, Any]] = p_config.get_object("functions") or []
        functions_dict = (
            {func["app_name"]: AzureFunction.model_validate(func) for func in functions_list}
            if functions_list
            else None
        )

        return cls(
            openai_models=p_config.get_object("openai_models"),
            container_apps=container_apps_dict,
            functions=functions_dict,
            app_service_plans=p_config.get_object("app_service_plans"),
            easy_auth_configs=p_config.get_object("easy_auth_configs") or {},
        )


COMMON_CONFIG = CommonPulumiConfig.from_pulumi_config()
