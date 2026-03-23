from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from pulumi_azure_native import containerregistry
from pulumi_azure_native import resources
from pulumi_command import local as command

from ms.infra.utils.container_apps import create_container_apps
from ms.infra.utils.container_apps import create_single_container_app
from ms.infra.utils.functions import deploy_azure_functions
from ms.infra.utils.models.app_service_plan import AppServicePlanConfig
from ms.infra.utils.models.azure_function import AzureFunction
from ms.infra.utils.models.container_app import ContainerApp
from ms.infra.utils.roles import BuiltInRole

_FUNCTION_CONFIG = AzureFunction(
    app_name="test-func",
    dockerfile_path="infra/docker/Dockerfile",
    docker_build_context="py",
    app_path="apps/test-func",
    plan="test-plan",
)

_PLAN_CONFIG = AppServicePlanConfig(
    sku_name="EP1",
    sku_tier="ElasticPremium",
    maximum_elastic_worker_count=1,
)

_CONTAINER_APP_CONFIG = ContainerApp(
    app_name="test-ca",
    dockerfile_path="infra/docker/Dockerfile",
    docker_build_context="ts",
    app_path="apps/test-ca",
    replicas_min=1,
    replicas_max=3,
)


class TestDeployAzureFunctionsSharedAcr:
    """When a shared ACR is provided, deploy_azure_functions must use it
    instead of creating its own. When omitted, it must create one internally."""

    @pytest.mark.parametrize(
        ("provide_shared_acr", "expect_internal_acr_created"),
        [
            pytest.param(True, False, id="shared ACR provided — no internal ACR"),
            pytest.param(False, True, id="no shared ACR — creates internal ACR"),
        ],
    )
    @patch("ms.infra.utils.functions.create_single_azure_function")
    @patch("ms.infra.utils.functions.create_app_service_plan")
    @patch("ms.infra.utils.functions.COMMON_CONFIG")
    @patch("ms.infra.utils.functions.create_and_login_acr")
    def test_internal_acr_creation(
        self,
        mock_create_acr: MagicMock,
        mock_config: MagicMock,
        _mock_create_plan: MagicMock,
        _mock_create_func: MagicMock,
        provide_shared_acr: bool,
        expect_internal_acr_created: bool,
    ) -> None:
        mock_config.functions = {"test-func": _FUNCTION_CONFIG}
        mock_config.app_service_plans = {"test-plan": _PLAN_CONFIG}
        mock_create_acr.return_value = (MagicMock(), MagicMock())

        rg = MagicMock(spec=resources.ResourceGroup)
        kwargs: dict = {"resource_group": rg}
        if provide_shared_acr:
            kwargs["acr"] = MagicMock(spec=containerregistry.Registry)
            kwargs["acr_login"] = MagicMock(spec=command.Command)

        deploy_azure_functions(**kwargs)

        if expect_internal_acr_created:
            mock_create_acr.assert_called_once()
        else:
            mock_create_acr.assert_not_called()


class TestCreateContainerAppsSharedAcr:
    """When a shared ACR is provided, create_container_apps must use it
    instead of creating its own. When omitted, it must create one internally."""

    @pytest.mark.parametrize(
        ("provide_shared_acr", "expect_internal_acr_created"),
        [
            pytest.param(True, False, id="shared ACR provided — no internal ACR"),
            pytest.param(False, True, id="no shared ACR — creates internal ACR"),
        ],
    )
    @patch("ms.infra.utils.container_apps.create_single_container_app")
    @patch("ms.infra.utils.container_apps.app.ManagedEnvironment")
    @patch("ms.infra.utils.container_apps.COMMON_CONFIG")
    @patch("ms.infra.utils.container_apps.create_and_login_acr")
    def test_internal_acr_creation(
        self,
        mock_create_acr: MagicMock,
        mock_config: MagicMock,
        _mock_env: MagicMock,
        _mock_create_ca: MagicMock,
        provide_shared_acr: bool,
        expect_internal_acr_created: bool,
    ) -> None:
        mock_config.container_apps = {"test-ca": _CONTAINER_APP_CONFIG}
        mock_create_acr.return_value = (MagicMock(), MagicMock())

        rg = MagicMock(spec=resources.ResourceGroup)
        kwargs: dict = {"resource_group": rg}
        if provide_shared_acr:
            kwargs["acr"] = MagicMock(spec=containerregistry.Registry)
            kwargs["acr_login"] = MagicMock(spec=command.Command)

        create_container_apps(**kwargs)

        if expect_internal_acr_created:
            mock_create_acr.assert_called_once()
        else:
            mock_create_acr.assert_not_called()


class TestCreateContainerAppsSharedEnvironment:
    """When a shared ManagedEnvironment is provided, create_container_apps must
    use it instead of creating its own. When omitted, it must create one internally."""

    @pytest.mark.parametrize(
        ("provide_shared_env", "expect_internal_env_created"),
        [
            pytest.param(True, False, id="shared env provided — no internal env"),
            pytest.param(False, True, id="no shared env — creates internal env"),
        ],
    )
    @patch("ms.infra.utils.container_apps.create_single_container_app")
    @patch("ms.infra.utils.container_apps.app.ManagedEnvironment")
    @patch("ms.infra.utils.container_apps.operationalinsights.get_shared_keys_output")
    @patch("ms.infra.utils.container_apps.operationalinsights.Workspace")
    @patch("ms.infra.utils.container_apps.COMMON_CONFIG")
    @patch("ms.infra.utils.container_apps.create_and_login_acr")
    def test_internal_env_creation(
        self,
        mock_create_acr: MagicMock,
        mock_config: MagicMock,
        mock_workspace: MagicMock,
        _mock_get_keys: MagicMock,
        mock_env_cls: MagicMock,
        _mock_create_ca: MagicMock,
        provide_shared_env: bool,
        expect_internal_env_created: bool,
    ) -> None:
        mock_config.container_apps = {"test-ca": _CONTAINER_APP_CONFIG}
        mock_create_acr.return_value = (MagicMock(), MagicMock())

        rg = MagicMock(spec=resources.ResourceGroup)
        kwargs: dict = {"resource_group": rg}
        if provide_shared_env:
            kwargs["container_apps_environment"] = MagicMock()

        create_container_apps(**kwargs)

        if expect_internal_env_created:
            mock_workspace.assert_called_once()
            mock_env_cls.assert_called_once()
        else:
            mock_workspace.assert_not_called()
            mock_env_cls.assert_not_called()


class TestCreateContainerAppsSharedWorkspace:
    """When a shared Log Analytics workspace is provided, create_container_apps must
    use it instead of creating its own. When omitted, it must create one internally."""

    @pytest.mark.parametrize(
        ("provide_shared_workspace", "expect_internal_workspace_created"),
        [
            pytest.param(True, False, id="shared workspace provided — no internal workspace"),
            pytest.param(False, True, id="no shared workspace — creates internal workspace"),
        ],
    )
    @patch("ms.infra.utils.container_apps.create_single_container_app")
    @patch("ms.infra.utils.container_apps.app.ManagedEnvironment")
    @patch("ms.infra.utils.container_apps.operationalinsights.get_shared_keys_output")
    @patch("ms.infra.utils.container_apps.operationalinsights.Workspace")
    @patch("ms.infra.utils.container_apps.COMMON_CONFIG")
    @patch("ms.infra.utils.container_apps.create_and_login_acr")
    def test_internal_workspace_creation(
        self,
        mock_create_acr: MagicMock,
        mock_config: MagicMock,
        mock_workspace_cls: MagicMock,
        _mock_get_keys: MagicMock,
        _mock_env: MagicMock,
        _mock_create_ca: MagicMock,
        provide_shared_workspace: bool,
        expect_internal_workspace_created: bool,
    ) -> None:
        mock_config.container_apps = {"test-ca": _CONTAINER_APP_CONFIG}
        mock_create_acr.return_value = (MagicMock(), MagicMock())

        rg = MagicMock(spec=resources.ResourceGroup)
        kwargs: dict = {"resource_group": rg}
        if provide_shared_workspace:
            kwargs["log_analytics_workspace"] = MagicMock()

        create_container_apps(**kwargs)

        if expect_internal_workspace_created:
            mock_workspace_cls.assert_called_once()
        else:
            mock_workspace_cls.assert_not_called()


class TestContainerAppAcrPullIdentity:
    """create_single_container_app uses a user-assigned managed identity
    with ACR Pull role for registry authentication instead of admin credentials."""

    @patch("ms.infra.utils.container_apps.pulumi")
    @patch("ms.infra.utils.container_apps.settings")
    @patch("ms.infra.utils.container_apps.build_docker_image")
    @patch("ms.infra.utils.container_apps.managedidentity")
    @patch("ms.infra.utils.container_apps.RoleAssignmentInfo")
    @patch("ms.infra.utils.container_apps.app")
    def test_creates_acr_pull_identity_and_role(
        self,
        mock_app_module: MagicMock,
        mock_role_info_cls: MagicMock,
        mock_mi_module: MagicMock,
        mock_build_image: MagicMock,
        mock_settings: MagicMock,
        _mock_pulumi: MagicMock,
    ) -> None:
        mock_settings.build_id = "test-build-id"
        mock_build_image.return_value = MagicMock(ref="test-image")

        rg = MagicMock(spec=resources.ResourceGroup)
        acr = MagicMock(spec=containerregistry.Registry)
        acr_login = MagicMock(spec=command.Command)

        create_single_container_app(
            container_app=_CONTAINER_APP_CONFIG,
            resource_group=rg,
            container_apps_environment=MagicMock(),
            acr=acr,
            acr_login=acr_login,
        )

        acr_pull_mi = mock_mi_module.UserAssignedIdentity.return_value

        # User-assigned identity created with app name prefix
        mock_mi_module.UserAssignedIdentity.assert_called_once_with(
            "test-ca-acr-pull-identity",
            resource_group_name=rg.name,
        )

        # ACR Pull role assigned to the managed identity
        mock_role_info_cls.assert_called_once_with(
            name="acr-pull",
            role=BuiltInRole.ACR_PULL,
            scope=acr.id,
        )
        mock_role_info_cls.return_value.create_service_principal_role_assignment.assert_called_once_with(
            principal_id=acr_pull_mi.principal_id,
            prefix="test-ca",
        )

    @patch("ms.infra.utils.container_apps.pulumi")
    @patch("ms.infra.utils.container_apps.settings")
    @patch("ms.infra.utils.container_apps.build_docker_image")
    @patch("ms.infra.utils.container_apps.managedidentity")
    @patch("ms.infra.utils.container_apps.RoleAssignmentInfo")
    @patch("ms.infra.utils.container_apps.app")
    def test_registry_uses_identity_not_admin_credentials(
        self,
        mock_app_module: MagicMock,
        _mock_role_info_cls: MagicMock,
        mock_mi_module: MagicMock,
        mock_build_image: MagicMock,
        mock_settings: MagicMock,
        _mock_pulumi: MagicMock,
    ) -> None:
        mock_settings.build_id = "test-build-id"
        mock_build_image.return_value = MagicMock(ref="test-image")

        acr = MagicMock(spec=containerregistry.Registry)

        create_single_container_app(
            container_app=_CONTAINER_APP_CONFIG,
            resource_group=MagicMock(spec=resources.ResourceGroup),
            container_apps_environment=MagicMock(),
            acr=acr,
            acr_login=MagicMock(spec=command.Command),
        )

        acr_pull_mi = mock_mi_module.UserAssignedIdentity.return_value

        # Registry credentials use identity (MI), not username/password
        mock_app_module.RegistryCredentialsArgs.assert_called_once_with(
            server=acr.login_server,
            identity=acr_pull_mi.id,
        )

        # No secrets configured (admin password removed)
        mock_app_module.SecretArgs.assert_not_called()

        # Container app identity includes user-assigned MI
        mock_app_module.ManagedServiceIdentityArgs.assert_called_once_with(
            type=mock_app_module.ManagedServiceIdentityType.SYSTEM_ASSIGNED_USER_ASSIGNED,
            user_assigned_identities=[acr_pull_mi.id],
        )
