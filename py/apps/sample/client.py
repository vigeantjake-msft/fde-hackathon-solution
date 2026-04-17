"""Azure AI Foundry client factory.

Single responsibility: build and cache the auth token provider and the
AsyncAzureOpenAI client itself.  Caching the client is critical for
latency: AsyncAzureOpenAI maintains an internal httpx connection pool,
so a fresh client per request forces a new TCP+TLS handshake (~50-150 ms)
on every call.  With a cached singleton the connection is reused after the
first warm-up, eliminating that overhead entirely.

Authentication uses DefaultAzureCredential (keyless) because the Foundry
account has disableLocalAuth=true.
"""

from functools import lru_cache

from azure.identity import DefaultAzureCredential
from azure.identity import get_bearer_token_provider
from openai import AsyncAzureOpenAI
from settings import settings


@lru_cache(maxsize=1)
def _token_provider():
    """Build a cached bearer-token provider from the ambient Azure credential.

    DefaultAzureCredential walks the chain: env vars → workload identity
    → managed identity → Azure CLI.  lru_cache ensures the credential is
    resolved once; token refresh is handled transparently by azure-identity.
    """
    credential = DefaultAzureCredential(
        # Exclude slow credential types not available in Container Apps to
        # reduce the time spent walking the chain on first use.
        exclude_visual_studio_code_credential=True,
        exclude_shared_token_cache_credential=True,
        exclude_interactive_browser_credential=True,
        exclude_azure_powershell_credential=True,
        exclude_azure_developer_cli_credential=True,
    )
    return get_bearer_token_provider(
        credential, "https://cognitiveservices.azure.com/.default"
    )


@lru_cache(maxsize=1)
def get_client() -> AsyncAzureOpenAI:
    """Return a shared AsyncAzureOpenAI client (singleton per process).

    Caching is intentional: the client owns an httpx connection pool that
    is reused across all requests.  A fresh client per request would pay a
    TCP+TLS round-trip (~50-150 ms) on every call even though the server
    did not change.

    The token provider handles token refresh automatically, so the cached
    client remains valid across token expiry boundaries.
    """
    az = settings.azure
    return AsyncAzureOpenAI(
        azure_endpoint=az.endpoint,
        azure_ad_token_provider=_token_provider(),
        api_version=az.api_version,
        # Increase connection pool size to match FDEBench concurrency (10+)
        # so concurrent requests share warm connections rather than queuing.
        max_retries=0,  # retries are handled by chat_with_retry in utils.py
        http_client=_build_http_client(),
    )


def _build_http_client():
    """Build an httpx client with a connection pool sized for concurrent use."""
    import httpx

    return httpx.AsyncClient(
        limits=httpx.Limits(
            max_connections=20,        # pool ceiling
            max_keepalive_connections=10,  # warm connections kept alive
            keepalive_expiry=30,       # seconds before idle connection closed
        ),
        timeout=httpx.Timeout(
            connect=10.0,
            read=None,   # no read timeout — model inference takes variable time
            write=10.0,
            pool=5.0,
        ),
    )
