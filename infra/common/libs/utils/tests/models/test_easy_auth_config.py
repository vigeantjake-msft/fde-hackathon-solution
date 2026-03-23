import pytest
from pydantic import ValidationError

from ms.infra.utils.models.easy_auth_config import EasyAuthConfig


class TestEasyAuthAppClientId:
    """easy_auth_app_client_id is optional but must be non-empty when provided."""

    @pytest.mark.parametrize(
        ("client_id", "expected_value"),
        [
            pytest.param(None, None, id="None — defaults to None"),
            pytest.param(
                "a4844a25-881f-45f9-8476-a0feb45745ea", "a4844a25-881f-45f9-8476-a0feb45745ea", id="valid UUID"
            ),
        ],
    )
    def test_accepts_valid_values(
        self,
        client_id: str | None,
        expected_value: str | None,
    ) -> None:
        config = EasyAuthConfig(
            easy_auth_app_client_id=client_id,
            allowed_app_client_ids=["some-app"],
        )
        assert config.easy_auth_app_client_id == expected_value

    def test_omitted_defaults_to_none(self) -> None:
        config = EasyAuthConfig(allowed_app_client_ids=["some-app"])
        assert config.easy_auth_app_client_id is None

    def test_rejects_empty_string(self) -> None:
        with pytest.raises(ValidationError, match="String should have at least 1 character"):
            EasyAuthConfig(
                easy_auth_app_client_id="",
                allowed_app_client_ids=["some-app"],
            )
