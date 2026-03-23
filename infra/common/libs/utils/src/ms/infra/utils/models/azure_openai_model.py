from enum import StrEnum

from pulumi_azure_native.cognitiveservices import DeploymentModelVersionUpgradeOption
from pydantic import Field

from ms.infra.core.models.base import FrozenBaseModel


class AzureOpenAiDeploymentSku(StrEnum):
    """Azure OpenAI deployment SKU types.

    See: https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/deployment-types
    """

    # Global deployments - data may be processed in any Azure AI Foundry location
    GLOBAL_STANDARD = "GlobalStandard"
    """Global Standard: Pay-per-call with dynamic routing to best availability datacenter."""

    GLOBAL_PROVISIONED = "GlobalProvisionedManaged"
    """Global Provisioned: Reserved capacity with global infrastructure."""

    GLOBAL_BATCH = "GlobalBatch"
    """Global Batch: Large-scale async processing at 50% lower cost."""

    # Data Zone deployments - data processed within Microsoft-specified data zone
    DATA_ZONE_STANDARD = "DataZoneStandard"
    """Data Zone Standard: Pay-per-call within data zone with dynamic routing."""

    DATA_ZONE_PROVISIONED = "DataZoneProvisionedManaged"
    """Data Zone Provisioned: Reserved capacity within data zone."""

    DATA_ZONE_BATCH = "DataZoneBatch"
    """Data Zone Batch: Large-scale async processing within data zone."""

    # Regional deployments - data stays in specified geography
    STANDARD = "Standard"
    """Standard: Regional pay-per-call, optimized for low-to-medium volume."""

    PROVISIONED = "ProvisionedManaged"
    """Regional Provisioned: Reserved regional capacity with specified throughput."""

    # Special purpose
    DEVELOPER = "DeveloperTier"
    """Developer: For fine-tuned model evaluation (no SLA or data residency guarantee)."""


class AzureOpenAiModel(FrozenBaseModel):
    model_name: str
    deployment_name: str
    capacity: int = Field(ge=0)
    version: str
    version_upgrade_option: DeploymentModelVersionUpgradeOption
    rai_policy_name: str | None = "Microsoft.Default"
    sku_name: AzureOpenAiDeploymentSku
