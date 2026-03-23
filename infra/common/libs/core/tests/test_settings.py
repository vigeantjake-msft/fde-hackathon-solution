import contextlib
from datetime import datetime
from pathlib import Path

import freezegun
import pytest

from ms.infra.core.settings import settings
from ms.infra.core.test_utils.mock_settings import mock_settings_attribute
from ms.infra.core.test_utils.mock_settings import mock_settings_property


@pytest.fixture(autouse=True)
def clear_build_id_cache() -> None:
    with contextlib.suppress(AttributeError):
        del settings.build_id


@freezegun.freeze_time(
    datetime(
        year=2024,
        month=1,
        day=2,
        hour=3,
        minute=4,
        second=5,
    )
)
@mock_settings_property("stack_name", "dev-myname")
def test_build_id_in_dev_stack() -> None:
    assert settings.build_id == "dev-myname-20240102030405"


@freezegun.freeze_time(
    datetime(
        year=2024,
        month=1,
        day=2,
        hour=3,
        minute=4,
        second=5,
    )
)
@mock_settings_property("stack_name", "staging")
@mock_settings_attribute("GITHUB_SHA", "198d4a8519fce4be845a1fc4881e3f852976c653")
def test_build_id_in_non_dev_stack() -> None:
    assert settings.build_id == "198d4a8-20240102030405"


@mock_settings_property("stack_name", "staging")
@mock_settings_attribute("GITHUB_SHA", None)
def test_build_id_raises_if_no_github_sha_in_non_dev_stack() -> None:
    with pytest.raises(RuntimeError, match="Expected GITHUB_SHA env var to be set for stack 'staging'"):
        _ = settings.build_id


@mock_settings_property("stack_name", "dev-test")
def test_build_id_is_cached_between_calls() -> None:
    call1 = settings.build_id
    call2 = settings.build_id

    assert call1 is call2


@mock_settings_property("stack_name", "dev-myname")
def test_stack_name_without_dev_prefix_dev_stack() -> None:
    assert settings.stack_name_without_dev_prefix == "myname"


@mock_settings_property("stack_name", "staging")
def test_stack_name_without_dev_prefix_non_dev_stack() -> None:
    assert settings.stack_name_without_dev_prefix == "staging"


def test_repo_root_finds_git_in_parent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """repo_root walks up to find the nearest .git directory."""
    # Simulate: tmp_path/.git exists, cwd is tmp_path/infra/platform/
    (tmp_path / ".git").mkdir()
    project_dir = tmp_path / "infra" / "platform"
    project_dir.mkdir(parents=True)

    monkeypatch.chdir(project_dir)
    assert settings.repo_root == tmp_path


def test_repo_root_raises_when_no_git_found(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """repo_root raises RuntimeError when no .git directory exists above cwd."""
    project_dir = tmp_path / "some" / "deep" / "path"
    project_dir.mkdir(parents=True)

    monkeypatch.chdir(project_dir)
    with pytest.raises(RuntimeError, match="Could not find repository root"):
        _ = settings.repo_root
