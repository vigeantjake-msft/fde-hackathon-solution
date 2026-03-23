from typing import Self

from pydantic import Field
from pydantic import model_validator

from ms.infra.core.models.base import FrozenBaseModel


class AppServicePlanConfig(FrozenBaseModel):
    """Configuration for an Azure App Service Plan.

    Each plan can be referenced by its dictionary key from Azure Function configurations.
    Multiple functions can share the same plan.
    """

    sku_name: str = Field(
        description="SKU name, e.g. 'B1', 'S1', 'P1v3', 'EP1'.",
    )

    sku_tier: str = Field(
        default="ElasticPremium",
        description="SKU tier, e.g. 'Basic', 'Standard', 'PremiumV3', 'ElasticPremium'.",
    )

    maximum_elastic_worker_count: int | None = Field(
        default=None,
        ge=1,
        description="Maximum number of instances the plan can scale out to. Only applicable to ElasticPremium tier.",
    )

    location: str | None = Field(
        default=None,
        description=(
            "Azure region for the App Service Plan. "
            "When omitted, inherits the default provider location (azure-native:location)."
        ),
    )

    @property
    def is_elastic_premium(self) -> bool:
        """Whether this plan uses the ElasticPremium tier."""
        return self.sku_tier == "ElasticPremium"

    @model_validator(mode="after")
    def _validate_elastic_worker_count(self) -> Self:
        """Forbid maximum_elastic_worker_count for non-ElasticPremium tiers."""
        if self.maximum_elastic_worker_count is not None and not self.is_elastic_premium:
            raise ValueError(
                f"maximum_elastic_worker_count is only applicable to ElasticPremium tier, "
                f"but sku_tier is '{self.sku_tier}'."
            )
        return self
