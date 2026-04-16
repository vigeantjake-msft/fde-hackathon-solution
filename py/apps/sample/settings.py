"""Application settings loaded from environment variables at startup.

Supports two configuration modes:

1. **Local dev** (default) — reads AZURE_OPENAI_ENDPOINT / AZURE_OPENAI_DEPLOYMENT
   directly, falls back to the dev Foundry account.

2. **Deployed (Container Apps)** — the platform injects AZURE_OPENAI_BACKENDS
   (a JSON array of backend objects), TRIAGE_MODEL, EXTRACT_MODEL, and
   ORCHESTRATE_MODEL.  These take precedence when present.

Example env (local):
    AZURE_OPENAI_ENDPOINT=https://my-foundry.cognitiveservices.azure.com/
    AZURE_OPENAI_DEPLOYMENT=gpt-4-1-mini
"""

import json
import os
from dataclasses import dataclass
from dataclasses import field

# Avoid a circular import: exceptions depends on nothing, so this is safe.
from exceptions import ConfigurationError


def _str(key: str, default: str) -> str:
    return os.environ.get(key, default)


def _int(key: str, default: int) -> int:
    raw = os.environ.get(key)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"Environment variable {key}={raw!r} must be an integer") from exc


def _float(key: str, default: float) -> float:
    raw = os.environ.get(key)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise ValueError(f"Environment variable {key}={raw!r} must be a float") from exc


def _primary_backend_endpoint() -> str:
    """Extract the primary endpoint from AZURE_OPENAI_BACKENDS if present.

    The platform injects a JSON array like:
      [{"name":"eastus2-primary","endpoint":"https://...","deployment":"gpt-4-1-mini",...}]

    Falls back to AZURE_OPENAI_ENDPOINT, then the dev Foundry default.
    """
    raw = os.environ.get("AZURE_OPENAI_BACKENDS")
    if raw:
        try:
            backends = json.loads(raw)
            if backends:
                return backends[0]["endpoint"]
        except (json.JSONDecodeError, KeyError, IndexError):
            pass
    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
    if not endpoint:
        raise ConfigurationError(
            "AZURE_OPENAI_ENDPOINT (or AZURE_OPENAI_BACKENDS) must be set. "
            "See .env.example for required environment variables."
        )
    return endpoint


# ---------------------------------------------------------------------------
# Config groups
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AzureSettings:
    """Connection config for Azure AI Foundry.

    Authentication uses DefaultAzureCredential (keyless) — works in both
    local dev (via az login) and Container Apps (via managed identity).
    """

    endpoint: str = field(default_factory=_primary_backend_endpoint)
    api_version: str = field(
        default_factory=lambda: _str("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
    )
    # Per-task model deployments — platform sets TRIAGE_MODEL etc. in Container Apps
    triage_deployment: str = field(
        default_factory=lambda: _str("TRIAGE_MODEL", _str("AZURE_OPENAI_DEPLOYMENT", "gpt-5.4"))
    )
    extract_deployment: str = field(
        default_factory=lambda: _str("EXTRACT_MODEL", _str("AZURE_OPENAI_DEPLOYMENT", "gpt-5.4"))
    )
    orchestrate_deployment: str = field(
        default_factory=lambda: _str("ORCHESTRATE_MODEL", _str("AZURE_OPENAI_DEPLOYMENT", "gpt-5.4"))
    )


@dataclass(frozen=True)
class ScoringSettings:
    """Values that affect the FDEBench scoring headers.

    X-Model-Name is read from TRIAGE_MODEL env var when available so the
    header always matches the actual model being used.
    """

    #: Returned in X-Model-Name response header.
    #: FDEBench maps this to a cost-tier score:
    #:   gpt-4-1-nano -> 1.0  |  gpt-4-1-mini -> 0.9  |  gpt-5.4 -> 0.75
    model_header: str = field(
        default_factory=lambda: _str(
            "TRIAGE_MODEL", _str("MODEL_HEADER", _str("AZURE_OPENAI_DEPLOYMENT", "gpt-5.4"))
        )
    )


@dataclass(frozen=True)
class OperationalSettings:
    """Runtime behaviour knobs."""

    #: Total attempts (including first try) before re-raising an Azure error.
    ai_max_retries: int = field(
        default_factory=lambda: _int("AI_MAX_RETRIES", 3)
    )
    #: Maximum LLM turns in the orchestration agentic loop.
    orchestrate_max_turns: int = field(
        default_factory=lambda: _int("ORCHESTRATE_MAX_TURNS", 40)
    )
    #: Per-call timeout in seconds for tool HTTP calls during orchestration.
    tool_call_timeout_s: float = field(
        default_factory=lambda: _float("TOOL_CALL_TIMEOUT_S", 30.0)
    )
    #: Hard timeout in seconds for each LLM API call (includes model inference).
    #: Set higher than expected P95 to avoid thrashing on slow models.
    llm_call_timeout_s: float = field(
        default_factory=lambda: _float("LLM_CALL_TIMEOUT_S", 120.0)
    )


@dataclass(frozen=True)
class Settings:
    """Top-level settings object, instantiated once at module import."""

    azure: AzureSettings = field(default_factory=AzureSettings)
    scoring: ScoringSettings = field(default_factory=ScoringSettings)
    ops: OperationalSettings = field(default_factory=OperationalSettings)


# ---------------------------------------------------------------------------
# Singleton — import and use directly:   from settings import settings
# ---------------------------------------------------------------------------

settings = Settings()
