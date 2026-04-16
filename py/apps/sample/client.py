"""Azure AI Foundry client factory.

Single responsibility: build and cache the auth token provider, then
vend a fresh AsyncAzureOpenAI instance on each call.  All connection
parameters are read from settings so they can be overridden via
environment variables without touching code.

Authentication uses DefaultAzureCredential (keyless) because the Foundry
account has disableLocalAuth=true — API-key auth is disabled at the
resource level.
"""

from functools import lru_cache

from azure.identity import DefaultAzureCredential
from azure.identity import get_bearer_token_provider
from openai import AsyncAzureOpenAI
from settings import settings


@lru_cache(maxsize=1)
def _token_provider():
    """Build a cached bearer-token provider from the ambient Azure credential.

    DefaultAzureCredential walks the chain: env vars -> workload identity
    -> managed identity -> Azure CLI.  In this environment the Azure CLI
    credential (az login) is used.  lru_cache ensures the credential is
    resolved once; token refresh is handled transparently by the library.
    """
    credential = DefaultAzureCredential()
    return get_bearer_token_provider(
        credential, "https://cognitiveservices.azure.com/.default"
    )


def get_client() -> AsyncAzureOpenAI:
    """Return an AsyncAzureOpenAI client configured from settings.

    A new client object is created per call (cheap — no network I/O),
    but the underlying token provider and credential are cached.
    """
    az = settings.azure
    return AsyncAzureOpenAI(
        azure_endpoint=az.endpoint,
        azure_ad_token_provider=_token_provider(),
        api_version=az.api_version,
    )
