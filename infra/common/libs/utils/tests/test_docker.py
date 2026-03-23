from unittest.mock import MagicMock
from unittest.mock import patch

from pulumi_azure_native.resources import ResourceGroup

from ms.infra.utils.docker import create_and_login_acr


class TestCreateAndLoginAcr:
    @patch("ms.infra.utils.docker.command.Command")
    @patch("ms.infra.utils.docker.pulumi")
    @patch("ms.infra.utils.docker.containerregistry")
    def test_admin_user_disabled(
        self,
        mock_cr: MagicMock,
        _mock_pulumi: MagicMock,
        _mock_cmd: MagicMock,
    ) -> None:
        rg = MagicMock(spec=ResourceGroup)
        create_and_login_acr(rg)

        assert mock_cr.Registry.call_args.kwargs["admin_user_enabled"] is False
