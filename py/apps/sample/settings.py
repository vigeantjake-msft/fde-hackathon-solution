"""Application settings with full type safety via pydantic-settings.

All values are read from environment variables with validation at startup.
No defaults are provided for required infrastructure secrets — a missing
AZURE_OPENAI_ENDPOINT (or AZURE_OPENAI_BACKENDS) raises a startup error
before the server accepts any traffic.

Example (.env or shell export):
    AZURE_OPENAI_ENDPOINT=https://my-foundry.openai.azure.com/
    TRIAGE_MODEL=gpt-4-1-mini
    EXTRACT_MODEL=gpt-4-1-mini
    ORCHESTRATE_MODEL=gpt-4-1-mini

See .env.example for the full list of supported variables.
"""

from __future__ import annotations

import json
import logging

from pydantic import Field
from pydantic import field_validator
from pydantic import model_validator
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict

logger = logging.getLogger(__name__)

# Sentinel used when no endpoint is resolvable.
_UNSET = ""


class AzureSettings(BaseSettings):
    """Connection config for Azure AI Foundry.

    Authentication uses DefaultAzureCredential (keyless) — works in local dev
    (az login) and Azure Container Apps (system-assigned managed identity).

    Endpoint priority:
      1. AZURE_OPENAI_BACKENDS JSON array (platform-injected in Container Apps)
      2. AZURE_OPENAI_ENDPOINT (direct override)
    Both raise a validation error when neither is set.
    """

    model_config = SettingsConfigDict(env_prefix="", extra="ignore", frozen=True)

    azure_openai_backends: str = Field(default="", alias="AZURE_OPENAI_BACKENDS")
    azure_openai_endpoint: str = Field(default="", alias="AZURE_OPENAI_ENDPOINT")
    azure_openai_api_version: str = Field(
        default="2024-12-01-preview", alias="AZURE_OPENAI_API_VERSION"
    )
    triage_deployment: str = Field(default="gpt-4-1-mini", alias="TRIAGE_MODEL")
    extract_deployment: str = Field(default="gpt-4-1-mini", alias="EXTRACT_MODEL")
    orchestrate_deployment: str = Field(default="gpt-4-1-mini", alias="ORCHESTRATE_MODEL")

    @model_validator(mode="after")
    def resolve_endpoint(self) -> AzureSettings:
        """Resolve endpoint from AZURE_OPENAI_BACKENDS or AZURE_OPENAI_ENDPOINT."""
        if not self.azure_openai_backends and not self.azure_openai_endpoint:
            raise ValueError(
                "Either AZURE_OPENAI_ENDPOINT or AZURE_OPENAI_BACKENDS must be set. "
                "See .env.example for required environment variables."
            )
        return self

    @property
    def endpoint(self) -> str:
        """Return the resolved Azure OpenAI endpoint."""
        if self.azure_openai_backends:
            try:
                backends = json.loads(self.azure_openai_backends)
                if backends and "endpoint" in backends[0]:
                    return backends[0]["endpoint"]
            except (json.JSONDecodeError, KeyError, IndexError) as exc:
                logger.warning("Failed to parse AZURE_OPENAI_BACKENDS: %s", exc)
        return self.azure_openai_endpoint

    @property
    def api_version(self) -> str:
        return self.azure_openai_api_version


class ScoringSettings(BaseSettings):
    """Values that affect the FDEBench scoring headers.

    X-Model-Name is returned on every response so the benchmark can
    compute the cost-tier score.  Defaults to TRIAGE_MODEL so the header
    always reflects the actual model being used.

    Cost tier reference:
      gpt-4.1-nano / gpt-5.4-nano  → 1.0
      gpt-4.1-mini / gpt-4o-mini   → 0.9
      gpt-4.1 / gpt-4o / gpt-5.4  → 0.75
    """

    model_config = SettingsConfigDict(env_prefix="", extra="ignore", frozen=True)

    model_header: str = Field(default="gpt-4-1-mini", alias="MODEL_HEADER")
    triage_model: str = Field(default="gpt-4-1-mini", alias="TRIAGE_MODEL")

    @model_validator(mode="after")
    def derive_model_header(self) -> ScoringSettings:
        """Use TRIAGE_MODEL as the default X-Model-Name header."""
        if not self.model_header or self.model_header == "gpt-4-1-mini":
            object.__setattr__(self, "model_header", self.triage_model)
        return self


class OperationalSettings(BaseSettings):
    """Runtime behaviour knobs — all have safe defaults."""

    model_config = SettingsConfigDict(env_prefix="", extra="ignore", frozen=True)

    #: Total attempts (including first try) before re-raising an Azure error.
    ai_max_retries: int = Field(default=3, alias="AI_MAX_RETRIES", ge=1, le=10)
    #: Maximum LLM turns in the orchestration agentic loop.
    orchestrate_max_turns: int = Field(default=40, alias="ORCHESTRATE_MAX_TURNS", ge=1, le=100)
    #: Per-call timeout for tool HTTP calls during orchestration.
    tool_call_timeout_s: float = Field(default=30.0, alias="TOOL_CALL_TIMEOUT_S", gt=0)
    #: Hard timeout for each LLM API call (includes model inference).
    llm_call_timeout_s: float = Field(default=120.0, alias="LLM_CALL_TIMEOUT_S", gt=0)

    @field_validator("ai_max_retries", "orchestrate_max_turns", mode="before")
    @classmethod
    def coerce_int(cls, v: object) -> int:
        return int(v)

    @field_validator("tool_call_timeout_s", "llm_call_timeout_s", mode="before")
    @classmethod
    def coerce_float(cls, v: object) -> float:
        return float(v)


class Settings(BaseSettings):
    """Top-level settings — instantiated once at module import."""

    model_config = SettingsConfigDict(env_prefix="", extra="ignore", frozen=True)

    azure: AzureSettings = Field(default_factory=AzureSettings)
    scoring: ScoringSettings = Field(default_factory=ScoringSettings)
    ops: OperationalSettings = Field(default_factory=OperationalSettings)


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

#: Import and use directly:   from settings import settings
settings = Settings()
