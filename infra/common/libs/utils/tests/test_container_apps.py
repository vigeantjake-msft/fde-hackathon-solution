from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from pulumi_azure_native import app
from pulumi_azure_native import containerregistry
from pulumi_azure_native import resources
from pulumi_command import local as command

from ms.infra.utils.container_apps import create_single_container_app
from ms.infra.utils.easy_auth import configure_container_app_easy_auth
from ms.infra.utils.models.container_app import ContainerApp
from ms.infra.utils.models.easy_auth_config import EasyAuthConfig

_CONTAINER_APP_CONFIG = ContainerApp(
    app_name="test-ca",
    dockerfile_path="infra/docker/Dockerfile",
    docker_build_context="ts",
    app_path="apps/test-ca",
    replicas_min=1,
    replicas_max=3,
)


class TestContainerAppEasyAuth:
    """Easy Auth for Container Apps is opt-in: configured only when
    COMMON_CONFIG.easy_auth_configs contains an entry for the app."""

    @pytest.mark.parametrize(
        ("provide_easy_auth_config", "expect_easy_auth_configured"),
        [
            pytest.param(True, True, id="easy auth config present — auth configured"),
            pytest.param(False, False, id="no easy auth config — auth skipped"),
        ],
    )
    @patch("ms.infra.utils.container_apps.configure_container_app_easy_auth")
    @patch("ms.infra.utils.container_apps.COMMON_CONFIG")
    @patch("ms.infra.utils.container_apps.pulumi")
    @patch("ms.infra.utils.container_apps.settings")
    @patch("ms.infra.utils.container_apps.build_docker_image")
    @patch("ms.infra.utils.container_apps.managedidentity")
    @patch("ms.infra.utils.container_apps.RoleAssignmentInfo")
    @patch("ms.infra.utils.container_apps.app")
    def test_easy_auth_opt_in(
        self,
        mock_app_module: MagicMock,
        _mock_role_info_cls: MagicMock,
        mock_mi_module: MagicMock,
        mock_build_image: MagicMock,
        mock_settings: MagicMock,
        _mock_pulumi: MagicMock,
        mock_config: MagicMock,
        mock_configure_easy_auth: MagicMock,
        provide_easy_auth_config: bool,
        expect_easy_auth_configured: bool,
    ) -> None:
        mock_settings.build_id = "test-build-id"
        mock_build_image.return_value = MagicMock(ref="test-image")

        easy_auth_config = EasyAuthConfig(
            easy_auth_app_client_id="test-client-id",
            allowed_app_client_ids=["allowed-app-id"],
        )
        mock_config.easy_auth_configs = {"test-ca": easy_auth_config} if provide_easy_auth_config else {}

        create_single_container_app(
            container_app=_CONTAINER_APP_CONFIG,
            resource_group=MagicMock(spec=resources.ResourceGroup),
            container_apps_environment=MagicMock(),
            acr=MagicMock(spec=containerregistry.Registry),
            acr_login=MagicMock(spec=command.Command),
        )

        if expect_easy_auth_configured:
            mock_configure_easy_auth.assert_called_once()
            call_kwargs = mock_configure_easy_auth.call_args.kwargs
            assert call_kwargs["app_name"] == "test-ca"
            assert call_kwargs["easy_auth_config"] is easy_auth_config
        else:
            mock_configure_easy_auth.assert_not_called()


class TestContainerAppEasyAuthClientIdEnforcement:
    """Non-dev stacks must provide easy_auth_app_client_id when Easy Auth is configured,
    because the CI service principal may lack Application.ReadWrite.All for auto-creation."""

    @patch("ms.infra.utils.easy_auth.settings")
    def test_non_dev_stack_rejects_missing_client_id(
        self,
        mock_settings: MagicMock,
    ) -> None:
        mock_settings.is_dev_stack = False
        mock_settings.stack_name = "staging"

        config = EasyAuthConfig(
            easy_auth_app_client_id=None,
            allowed_app_client_ids=["allowed-app"],
        )

        with pytest.raises(AssertionError, match="easy_auth_app_client_id is required"):
            configure_container_app_easy_auth(
                container_app=MagicMock(spec=app.ContainerApp),
                resource_group_name="test-rg",
                app_name="test-ca",
                easy_auth_config=config,
            )

    @patch("ms.infra.utils.easy_auth.get_or_create_app_registration")
    @patch("ms.infra.utils.easy_auth.app.ContainerAppsAuthConfig")
    @patch("ms.infra.utils.easy_auth.settings")
    def test_dev_stack_allows_missing_client_id(
        self,
        mock_settings: MagicMock,
        _mock_auth_config: MagicMock,
        mock_get_or_create: MagicMock,
    ) -> None:
        mock_settings.is_dev_stack = True
        mock_settings.tenant_id = "mock-tenant-id"
        mock_get_or_create.return_value = MagicMock()

        config = EasyAuthConfig(
            easy_auth_app_client_id=None,
            allowed_app_client_ids=["allowed-app"],
        )

        configure_container_app_easy_auth(
            container_app=MagicMock(spec=app.ContainerApp),
            resource_group_name="test-rg",
            app_name="test-ca",
            easy_auth_config=config,
        )
