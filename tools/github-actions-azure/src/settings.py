import functools

from pulumi_azure_native import authorization
from pulumi_azure_native.authorization import AwaitableGetClientConfigResult
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    MANAGED_IDENTITY_CLIENT_ID: str
    MANAGED_IDENTITY_RESOURCE_GROUP_NAME: str

    # Whether this script is running in a GitHub Actions CI environment
    GITHUB_ACTIONS: bool

    @functools.cached_property
    def _client_config(self) -> AwaitableGetClientConfigResult:
        return authorization.get_client_config()

    @property
    def subscription_id(self) -> str:
        return self._client_config.subscription_id

    @property
    def tenant_id(self) -> str:
        return self._client_config.tenant_id


settings = Settings()  # pyright: ignore[reportCallIssue]
