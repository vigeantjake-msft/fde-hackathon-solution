from typing import Any

import pytest

from ms.infra.utils.models.app_service_plan import AppServicePlanConfig


class TestAppServicePlanConfig:
    def test_accepts_elastic_premium_config(self) -> None:
        config = AppServicePlanConfig(sku_name="EP2", sku_tier="ElasticPremium", maximum_elastic_worker_count=10)
        assert config.sku_name == "EP2"
        assert config.sku_tier == "ElasticPremium"
        assert config.maximum_elastic_worker_count == 10

    def test_accepts_basic_config(self) -> None:
        config = AppServicePlanConfig(sku_name="B1", sku_tier="Basic")
        assert config.sku_name == "B1"
        assert config.sku_tier == "Basic"
        assert config.maximum_elastic_worker_count is None

    def test_location_defaults_to_none(self) -> None:
        config = AppServicePlanConfig(sku_name="EP1", sku_tier="ElasticPremium", maximum_elastic_worker_count=1)
        assert config.location is None

    def test_accepts_explicit_location(self) -> None:
        config = AppServicePlanConfig(
            sku_name="EP1", sku_tier="ElasticPremium", maximum_elastic_worker_count=1, location="SwedenCentral"
        )
        assert config.location == "SwedenCentral"

    def test_sku_tier_defaults_to_elastic_premium(self) -> None:
        config = AppServicePlanConfig(sku_name="EP1")
        assert config.sku_tier == "ElasticPremium"

    @pytest.mark.parametrize(
        "kwargs",
        [
            pytest.param({"sku_tier": "Basic"}, id="missing-sku-name"),
            pytest.param({}, id="missing-all-fields"),
        ],
    )
    def test_rejects_missing_required_fields(self, kwargs: dict[str, Any]) -> None:
        with pytest.raises(ValueError):
            AppServicePlanConfig(**kwargs)  # type: ignore[arg-type]

    def test_rejects_worker_count_below_minimum(self) -> None:
        with pytest.raises(ValueError):
            AppServicePlanConfig(sku_name="EP1", sku_tier="ElasticPremium", maximum_elastic_worker_count=0)

    def test_rejects_worker_count_on_non_elastic_tier(self) -> None:
        with pytest.raises(ValueError, match="only applicable to ElasticPremium tier"):
            AppServicePlanConfig(sku_name="B1", sku_tier="Basic", maximum_elastic_worker_count=3)
