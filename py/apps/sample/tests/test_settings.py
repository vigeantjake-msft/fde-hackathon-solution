"""Tests for settings.py — default values and env-var overrides."""

import os
from unittest.mock import patch

import pytest

from exceptions import ConfigurationError
from settings import AzureSettings
from settings import OperationalSettings
from settings import ScoringSettings
from settings import Settings


class TestAzureSettingsDefaults:
    """Azure settings read from the env; no hardcoded prod endpoint defaults."""

    def test_endpoint_raises_without_env(self):
        """AZURE_OPENAI_ENDPOINT is required — no default to prevent misconfiguration."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove all relevant env vars
            env_without = {
                k: v for k, v in os.environ.items()
                if k not in ("AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_BACKENDS")
            }
            with patch.dict(os.environ, env_without, clear=True):
                with pytest.raises(ConfigurationError, match="AZURE_OPENAI_ENDPOINT"):
                    AzureSettings()

    def test_default_api_version(self):
        s = AzureSettings()
        assert s.api_version == "2025-01-01-preview"

    def test_triage_deployment_reads_triage_model(self):
        with patch.dict(os.environ, {"TRIAGE_MODEL": "gpt-5.4"}):
            s = AzureSettings()
            assert s.triage_deployment == "gpt-5.4"

    def test_extract_deployment_reads_extract_model(self):
        with patch.dict(os.environ, {"EXTRACT_MODEL": "gpt-4-1-mini"}):
            s = AzureSettings()
            assert s.extract_deployment == "gpt-4-1-mini"

    def test_orchestrate_deployment_reads_orchestrate_model(self):
        with patch.dict(os.environ, {"ORCHESTRATE_MODEL": "gpt-4-1-mini"}):
            s = AzureSettings()
            assert s.orchestrate_deployment == "gpt-4-1-mini"


class TestAzureSettingsEnvOverrides:
    """Azure settings read from environment variables when present."""

    def test_endpoint_override(self):
        with patch.dict(os.environ, {"AZURE_OPENAI_ENDPOINT": "https://custom.azure.com/"}):
            s = AzureSettings()
            assert s.endpoint == "https://custom.azure.com/"

    def test_backends_takes_priority_over_endpoint(self):
        backends = '[{"endpoint": "https://from-backends.com/", "deployment": "gpt-test"}]'
        with patch.dict(os.environ, {
            "AZURE_OPENAI_BACKENDS": backends,
            "AZURE_OPENAI_ENDPOINT": "https://should-not-use.com/",
        }):
            s = AzureSettings()
            assert s.endpoint == "https://from-backends.com/"

    def test_api_version_override(self):
        with patch.dict(os.environ, {"AZURE_OPENAI_API_VERSION": "2024-02-01"}):
            s = AzureSettings()
            assert s.api_version == "2024-02-01"


class TestScoringSettingsDefaults:
    def test_model_header_reads_triage_model(self):
        with patch.dict(os.environ, {"TRIAGE_MODEL": "gpt-5.4"}):
            s = ScoringSettings()
            assert s.model_header == "gpt-5.4"

    def test_model_header_override(self):
        with patch.dict(os.environ, {"TRIAGE_MODEL": "gpt-4-1-mini"}):
            s = ScoringSettings()
            assert s.model_header == "gpt-4-1-mini"

    def test_explicit_model_header_env_var(self):
        with patch.dict(os.environ, {"MODEL_HEADER": "gpt-4-1-nano", "TRIAGE_MODEL": "gpt-5.4"}):
            # TRIAGE_MODEL takes precedence (read first in the chain)
            s = ScoringSettings()
            assert s.model_header == "gpt-5.4"


class TestOperationalSettingsDefaults:
    def test_default_max_retries(self):
        s = OperationalSettings()
        assert s.ai_max_retries == 3

    def test_default_orchestrate_max_turns(self):
        s = OperationalSettings()
        assert s.orchestrate_max_turns == 40

    def test_default_tool_call_timeout(self):
        s = OperationalSettings()
        assert s.tool_call_timeout_s == 30.0

    def test_default_llm_call_timeout(self):
        s = OperationalSettings()
        assert s.llm_call_timeout_s == 120.0

    def test_max_retries_override(self):
        with patch.dict(os.environ, {"AI_MAX_RETRIES": "5"}):
            s = OperationalSettings()
            assert s.ai_max_retries == 5

    def test_llm_timeout_override(self):
        with patch.dict(os.environ, {"LLM_CALL_TIMEOUT_S": "60.0"}):
            s = OperationalSettings()
            assert s.llm_call_timeout_s == 60.0


class TestSettingsIsFrozen:
    """Settings objects are frozen — mutation should raise."""

    def test_azure_settings_is_frozen(self):
        s = AzureSettings()
        with pytest.raises(Exception):
            s.api_version = "other"  # type: ignore[misc]

    def test_top_level_settings_is_frozen(self):
        s = Settings()
        with pytest.raises(Exception):
            s.ops = OperationalSettings()  # type: ignore[misc]
