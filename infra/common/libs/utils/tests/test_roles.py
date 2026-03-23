from ms.infra.core.test_utils.mock_settings import mock_settings_property
from ms.infra.utils.roles import BuiltInRole


@mock_settings_property("stack_name", "dev-test")
@mock_settings_property("subscription_id", "mock-sub-id")
def test_built_in_role_to_definition_id() -> None:
    assert (
        BuiltInRole.READER.to_definition_id() == "/subscriptions/mock-sub-id/providers/Microsoft.Authorization/"
        "roleDefinitions/acdd72a7-3385-48ef-bd42-f606fba81ae7"
    )
