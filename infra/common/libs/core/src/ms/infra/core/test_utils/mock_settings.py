from typing import Any
from unittest import mock


def mock_settings_property(name: str, value: Any):
    """
    Use this to mock a readonly property:

    ```
    class Settings(BaseSettings):
        @property
        def my_property(self) -> str:
            return "real_value"

    @mock_settings_property("my_property", "mocked_value")
    def test_something():
        assert settings.my_property == "mocked_value"
    ```
    """
    return mock.patch(
        f"ms.infra.core.settings.Settings.{name}",
        value,
    )


def mock_settings_attribute(name: str, value: Any):
    """
    Use this to mock an attribute:

    ```
    class Settings(BaseSettings):
        MY_FIELD: str

    @mock_settings_attribute("MY_FIELD", "mocked_value")
    def test_something():
        assert settings.MY_FIELD == "mocked_value"
    ```
    """
    return mock.patch(
        f"ms.infra.core.settings.settings.{name}",
        value,
    )
