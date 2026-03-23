from pydantic import Field

from ms.infra.utils.models.docker_config_base import DockerConfigBase


class AzureFunction(DockerConfigBase):
    """Base configuration for an Azure Function."""

    plan: str = Field(
        description="Name of the App Service Plan to deploy this function to. "
        "Must match a name defined in the app_service_plans configuration.",
    )

    is_durable: bool = Field(
        default=False,
        description="Whether this function uses Durable Functions for long-running workflows. "
        "When True, a storage account will be created and configured for orchestration state.",
    )

    runtime_scale_monitoring_enabled: bool = Field(
        default=True,
        description="Whether to enable runtime scale monitoring for extension-driven scale-out. "
        "Defaults to True for Elastic Premium plans, where real-time trigger signals (e.g. queue depth) "
        "provide faster scaling than timer-based polling. "
        "Must be set to False for Consumption or non-EP Dedicated plans, as Azure will reject the deployment.",
    )
