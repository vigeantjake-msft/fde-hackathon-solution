from collections.abc import Generator
from typing import Any
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from ms.infra.utils.models.app_service_plan import AppServicePlanConfig
from ms.infra.utils.models.common_pulumi_config import CommonPulumiConfig


@pytest.fixture
def mock_pulumi_config() -> Generator[MagicMock, None, None]:
    mock_config = MagicMock()
    mock_config.get_object.return_value = None
    mock_config.get.return_value = None
    with patch("ms.infra.utils.models.common_pulumi_config.pulumi.Config", return_value=mock_config):
        yield mock_config


@pytest.mark.usefixtures("mock_pulumi_config")
class TestFromPulumiConfigAppServicePlans:
    def test_returns_none_when_not_configured(self) -> None:
        config = CommonPulumiConfig.from_pulumi_config()
        assert config.app_service_plans is None

    @pytest.mark.parametrize(
        ("raw_config", "expected"),
        [
            pytest.param(
                {"custom": {"sku_name": "EP2", "tier": "ElasticPremium", "maximum_elastic_worker_count": 5}},
                {"custom": AppServicePlanConfig(sku_name="EP2", tier="ElasticPremium", maximum_elastic_worker_count=5)},
                id="single-plan",
            ),
            pytest.param(
                {
                    "default": {"sku_name": "B1", "tier": "Basic"},
                    "high-memory": {"sku_name": "EP3", "tier": "ElasticPremium", "maximum_elastic_worker_count": 20},
                },
                {
                    "default": AppServicePlanConfig(sku_name="B1", tier="Basic"),
                    "high-memory": AppServicePlanConfig(
                        sku_name="EP3", tier="ElasticPremium", maximum_elastic_worker_count=20
                    ),
                },
                id="multiple-plans",
            ),
            pytest.param(
                {
                    "custom": {
                        "sku_name": "EP1",
                        "tier": "ElasticPremium",
                        "maximum_elastic_worker_count": 5,
                        "location": "SwedenCentral",
                    }
                },
                {
                    "custom": AppServicePlanConfig(
                        sku_name="EP1", tier="ElasticPremium", maximum_elastic_worker_count=5, location="SwedenCentral"
                    )
                },
                id="plan-with-location-override",
            ),
        ],
    )
    def test_parses_plans_from_config(
        self,
        mock_pulumi_config: MagicMock,
        raw_config: dict[str, Any],
        expected: dict[str, AppServicePlanConfig],
    ) -> None:
        mock_pulumi_config.get_object.side_effect = lambda key: {"app_service_plans": raw_config}.get(key)

        config = CommonPulumiConfig.from_pulumi_config()

        assert config.app_service_plans == expected
