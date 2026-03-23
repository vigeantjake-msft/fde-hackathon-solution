import uuid
from collections.abc import Generator
from unittest.mock import MagicMock
from unittest.mock import patch

import pulumi
import pytest
from pulumi_azure_native import resources

from ms.infra.utils.foundry.deployments import _resolve_existing_account_name
from ms.infra.utils.foundry.deployments import deploy_foundry_with_project

# ---------------------------------------------------------------------------
# Tests for _resolve_existing_account_name
# ---------------------------------------------------------------------------


def test_resolve_existing_account_name_returns_name_when_account_exists() -> None:
    with patch(
        "ms.infra.utils.foundry.deployments.cognitiveservices.get_account",
        return_value=MagicMock(),
    ):
        result = _resolve_existing_account_name("myproject-dev", "rg-myproject-dev")

    assert result == "myproject-dev"


def test_resolve_existing_account_name_returns_none_when_account_missing() -> None:
    with patch(
        "ms.infra.utils.foundry.deployments.cognitiveservices.get_account",
        side_effect=Exception("AccountNotFound"),
    ):
        result = _resolve_existing_account_name("myproject-dev", "rg-myproject-dev")

    assert result is None


# ---------------------------------------------------------------------------
# Pulumi mocks for deploy_foundry_with_project tests
# ---------------------------------------------------------------------------


class _FoundryMocks(pulumi.runtime.Mocks):
    def __init__(self) -> None:
        self.created_resources: list[pulumi.runtime.MockResourceArgs] = []

    def new_resource(self, args: pulumi.runtime.MockResourceArgs) -> tuple[str, dict]:
        self.created_resources.append(args)
        outputs: dict[str, object] = {**args.inputs, "id": str(uuid.uuid4())}
        outputs["name"] = args.inputs.get("accountName", args.name)
        # RandomString needs a `result` output with the generated value.
        if args.typ == "random:index/randomString:RandomString":
            outputs["result"] = "a1b2c3"
        return args.name + "_id", outputs

    def call(self, args: pulumi.runtime.MockCallArgs) -> dict[str, object]:
        return {}


def _find_account_resource(mocks: _FoundryMocks) -> pulumi.runtime.MockResourceArgs | None:
    return next(
        (r for r in mocks.created_resources if r.typ.endswith(":cognitiveservices:Account")),
        None,
    )


_MOCK_CONFIG = MagicMock(openai_models=[])

# Patch COMMON_CONFIG for the entire module so it is active during Output.apply callbacks.
pytestmark = pytest.mark.usefixtures("_patch_common_config")


@pytest.fixture(autouse=True)
def _patch_common_config() -> Generator[None, None, None]:
    with patch("ms.infra.utils.foundry.deployments.COMMON_CONFIG", _MOCK_CONFIG):
        yield


# ---------------------------------------------------------------------------
# Tests for deploy_foundry_with_project
# ---------------------------------------------------------------------------


@pytest.fixture
def foundry_mocks_no_existing_account() -> Generator[_FoundryMocks, None, None]:
    """Mocks where the legacy Foundry account does NOT exist in Azure."""
    mocks = _FoundryMocks()
    pulumi.runtime.set_mocks(mocks)
    with patch(
        "ms.infra.utils.foundry.deployments.cognitiveservices.get_account",
        side_effect=Exception("not found"),
    ):
        yield mocks


@pytest.fixture
def foundry_mocks_with_existing_account() -> Generator[_FoundryMocks, None, None]:
    """Mocks where the legacy Foundry account ALREADY EXISTS in Azure."""
    mocks = _FoundryMocks()
    pulumi.runtime.set_mocks(mocks)
    with patch(
        "ms.infra.utils.foundry.deployments.cognitiveservices.get_account",
        return_value=MagicMock(),
    ):
        yield mocks


@pulumi.runtime.test
def test_deploy_foundry_new_account_uses_generated_name(
    foundry_mocks_no_existing_account: _FoundryMocks,
) -> None:
    """When no legacy account exists, accountName is the sanitized base + random suffix."""
    rg = resources.ResourceGroup("rg", resource_group_name="rg-myproject-dev", location="eastus")

    foundry_account, _ = deploy_foundry_with_project(rg)

    def _assert(args: dict[str, object]) -> None:
        acct = _find_account_resource(foundry_mocks_no_existing_account)
        assert acct is not None
        account_name = acct.inputs.get("accountName")
        assert isinstance(account_name, str)
        # Name starts with the sanitized logical name and ends with the random suffix.
        assert account_name.startswith("foundry")
        assert len(account_name) > len("foundry")

    pulumi.Output.all(name=foundry_account.account_name).apply(_assert)


@pulumi.runtime.test
def test_deploy_foundry_existing_account_keeps_legacy_name(
    foundry_mocks_with_existing_account: _FoundryMocks,
) -> None:
    """When the legacy account exists, accountName is set to the legacy {project}-{stack} name."""
    rg = resources.ResourceGroup("rg", resource_group_name="rg-myproject-dev", location="eastus")

    foundry_account, _ = deploy_foundry_with_project(rg)

    def _assert(args: dict[str, object]) -> None:
        acct = _find_account_resource(foundry_mocks_with_existing_account)
        assert acct is not None
        assert acct.inputs.get("accountName") == "project-stack"

    pulumi.Output.all(name=foundry_account.account_name).apply(_assert)


@pulumi.runtime.test
def test_deploy_foundry_new_account_subdomain_matches_resource_name(
    foundry_mocks_no_existing_account: _FoundryMocks,
) -> None:
    """When no legacy account exists, customSubDomainName falls back to the resolved resource name."""
    rg = resources.ResourceGroup("rg", resource_group_name="rg-myproject-dev", location="eastus")

    foundry_account, _ = deploy_foundry_with_project(rg)

    def _assert(args: dict[str, object]) -> None:
        acct = _find_account_resource(foundry_mocks_no_existing_account)
        assert acct is not None
        props = acct.inputs.get("properties", {})
        assert isinstance(props, dict)
        assert props.get("customSubDomainName") == acct.inputs.get("accountName")

    pulumi.Output.all(name=foundry_account.account_name).apply(_assert)


@pulumi.runtime.test
def test_deploy_foundry_existing_account_keeps_legacy_subdomain(
    foundry_mocks_with_existing_account: _FoundryMocks,
) -> None:
    """When the legacy account exists, customSubDomainName preserves the legacy {project}-{stack} name."""
    rg = resources.ResourceGroup("rg", resource_group_name="rg-myproject-dev", location="eastus")

    foundry_account, _ = deploy_foundry_with_project(rg)

    def _assert(args: dict[str, object]) -> None:
        acct = _find_account_resource(foundry_mocks_with_existing_account)
        assert acct is not None
        props = acct.inputs.get("properties", {})
        assert isinstance(props, dict)
        assert props.get("customSubDomainName") == "project-stack"

    pulumi.Output.all(name=foundry_account.account_name).apply(_assert)


@pulumi.runtime.test
def test_deploy_foundry_new_account_uses_default_project_name(
    foundry_mocks_no_existing_account: _FoundryMocks,
) -> None:
    """When no legacy account exists, defaultProject is 'default' instead of the legacy name."""
    rg = resources.ResourceGroup("rg", resource_group_name="rg-myproject-dev", location="eastus")

    foundry_account, _ = deploy_foundry_with_project(rg)

    def _assert(args: dict[str, object]) -> None:
        acct = _find_account_resource(foundry_mocks_no_existing_account)
        assert acct is not None
        props = acct.inputs.get("properties", {})
        assert isinstance(props, dict)
        assert props.get("defaultProject") == "default"
        assert props.get("associatedProjects") == ["default"]

    pulumi.Output.all(name=foundry_account.account_name).apply(_assert)


@pulumi.runtime.test
def test_deploy_foundry_existing_account_keeps_legacy_project_name(
    foundry_mocks_with_existing_account: _FoundryMocks,
) -> None:
    """When the legacy account exists, defaultProject preserves the legacy {project}-{stack} name."""
    rg = resources.ResourceGroup("rg", resource_group_name="rg-myproject-dev", location="eastus")

    foundry_account, _ = deploy_foundry_with_project(rg)

    def _assert(args: dict[str, object]) -> None:
        acct = _find_account_resource(foundry_mocks_with_existing_account)
        assert acct is not None
        props = acct.inputs.get("properties", {})
        assert isinstance(props, dict)
        assert props.get("defaultProject") == "project-stack"
        assert props.get("associatedProjects") == ["project-stack"]

    pulumi.Output.all(name=foundry_account.account_name).apply(_assert)
