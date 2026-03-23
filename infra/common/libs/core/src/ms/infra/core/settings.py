import functools
import os
import pathlib
from datetime import UTC
from datetime import datetime

import pulumi
from pulumi_azure_native import authorization
from pulumi_azure_native.authorization import AwaitableGetClientConfigResult
from pydantic_settings import BaseSettings

DEV_STACK_PREFIX = "dev-"


class Settings(BaseSettings):
    GITHUB_SHA: str | None = None

    @functools.cached_property
    def _client_config(self) -> AwaitableGetClientConfigResult:
        return authorization.get_client_config()

    @property
    def subscription_id(self) -> str:
        return self._client_config.subscription_id

    @property
    def tenant_id(self) -> str:
        return self._client_config.tenant_id

    @property
    def client_id(self) -> str:
        return self._client_config.client_id

    @property
    def stack_name(self) -> str:
        return pulumi.get_stack()

    @property
    def project_name(self) -> str:
        return pulumi.get_project()

    @property
    def is_dev_stack(self) -> bool:
        return self.stack_name.startswith(DEV_STACK_PREFIX)

    @property
    def stack_name_without_dev_prefix(self) -> str:
        if self.is_dev_stack:
            return self.stack_name[len(DEV_STACK_PREFIX) :]
        return self.stack_name

    @property
    def is_staging_stack(self) -> bool:
        return self.stack_name == "staging"

    @property
    def is_production_stack(self) -> bool:
        return self.stack_name == "production"

    @property
    def repo_root(self) -> pathlib.Path:
        """Get the repository root directory.

        Walks up from the current working directory (the Pulumi project directory)
        until it finds a ``.git`` directory, which marks the repository root.

        Supports both mono-project (``infra/app/``) and multi-project
        (``infra/projects/<name>/``) layouts.

        Note: We use cwd instead of __file__ because when infra-common-core is installed
        (even with path dependencies), __file__ points to the installed location in
        .venv/lib/python3.12/site-packages/, not the source location. Using cwd is
        reliable because Pulumi always runs from the project directory.
        """
        cwd = pathlib.Path(os.getcwd()).resolve()
        current = cwd
        while current != current.parent:
            if (current / ".git").exists():
                return current
            current = current.parent
        raise RuntimeError(f"Could not find repository root (no .git directory) starting from {cwd}")

    @functools.cached_property
    def build_id(self) -> str:
        """Generate a unique build ID for each deployment.

        For dev stacks, uses stack name and timestamp.
        For non-dev stacks, uses commit SHA and timestamp.
        """
        now = datetime.now(UTC).strftime("%Y%m%d%H%M%S")

        if self.is_dev_stack:
            # e.g. dev-alice-20240315123045
            return f"{self.stack_name}-{now}"

        # Non-dev stacks are created via GitHub Actions.
        if not self.GITHUB_SHA:
            raise RuntimeError(f"Expected GITHUB_SHA env var to be set for stack '{self.stack_name}'.")

        return f"{self.GITHUB_SHA[:7]}-{now}"


settings = Settings()
