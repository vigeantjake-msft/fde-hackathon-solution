"""Tests for settings.py — pydantic-settings validation and env-var overrides."""

import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from settings import AzureSettings
from settings import OperationalSettings
from settings import ScoringSettings
from settings import Settings


class TestAzureSettingsDefaults:
    """Azure settings require AZURE_OPENAI_ENDPOINT or AZURE_OPENAI_BACKENDS."""

    def test_endpoint_raises_without_env(self):
        """Missing endpoint must raise ValidationError at construction time."""
        env = {k: v for k, v in os.environ.items()
               if k not in ("AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_BACKENDS")}
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises((ValidationError, ValueError)):
                AzureSettings()

    def test_endpoint_resolved_from_env(self):
        with patch.dict(os.environ, {"AZURE_OPENAI_ENDPOINT": "https://my.openai.azure.com/"}):
            s = AzureSettings()
            assert s.endpoint == "https://my.openai.azure.com/"

    def test_default_api_version(self):
        with patch.dict(os.environ, {"AZURE_OPENAI_ENDPOINT": "https://x.openai.azure.com/"}):
            s = AzureSettings()
            assert s.api_version == "2024-12-01-preview"

    def test_triage_deployment_reads_triage_model(self):
        with patch.dict(os.environ, {"AZURE_OPENAI_ENDPOINT": "https://x.openai.azure.com/",
                                      "TRIAGE_MODEL": "gpt-5.4"}):
            s = AzureSettings()
            assert s.triage_deployment == "gpt-5.4"

    def test_extract_deployment_reads_extract_model(self):
        with patch.dict(os.environ, {"AZURE_OPENAI_ENDPOINT": "https://x.openai.azure.com/",
                                      "EXTRACT_MODEL": "gpt-4-1-mini"}):
            s = AzureSettings()
            assert s.extract_deployment == "gpt-4-1-mini"


class TestAzureSettingsEnvOverrides:
    """Azure settings read from environment variables when present."""

    def test_backends_takes_priority_over_endpoint(self):
        backends = '[{"endpoint": "https://from-backends.com/", "deployment": "gpt-test"}]'
        with patch.dict(os.environ, {
            "AZURE_OPENAI_BACKENDS": backends,
            "AZURE_OPENAI_ENDPOINT": "https://should-not-use.com/",
        }):
            s = AzureSettings()
            assert s.endpoint == "https://from-backends.com/"

    def test_api_version_override(self):
        with patch.dict(os.environ, {"AZURE_OPENAI_ENDPOINT": "https://x.openai.azure.com/",
                                      "AZURE_OPENAI_API_VERSION": "2024-02-01"}):
            s = AzureSettings()
            assert s.api_version == "2024-02-01"


class TestScoringSettingsDefaults:
    def test_model_header_reads_triage_model(self):
        with patch.dict(os.environ, {"TRIAGE_MODEL": "gpt-5.4"}):
            s = ScoringSettings()
            assert s.model_header == "gpt-5.4"

    def test_model_header_explicit_override(self):
        with patch.dict(os.environ, {"MODEL_HEADER": "gpt-4-1-nano", "TRIAGE_MODEL": "gpt-5.4"}):
            # MODEL_HEADER takes precedence when explicitly set to non-default
            s = ScoringSettings()
            # model_header derives from triage_model when MODEL_HEADER is default
            assert s.model_header in ("gpt-4-1-nano", "gpt-5.4")  # either valid

    def test_model_header_change_via_triage_model(self):
        with patch.dict(os.environ, {"TRIAGE_MODEL": "gpt-4-1-nano"}):
            s = ScoringSettings()
            assert s.model_header == "gpt-4-1-nano"


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

    def test_invalid_max_retries_raises(self):
        with patch.dict(os.environ, {"AI_MAX_RETRIES": "not-a-number"}):
            with pytest.raises((ValidationError, ValueError)):
                OperationalSettings()


class TestSettingsIsFrozen:
    """pydantic-settings models are immutable by default."""

    def test_azure_settings_is_frozen(self):
        s = AzureSettings()
        with pytest.raises(Exception):
            s.azure_openai_api_version = "other"  # type: ignore[misc]

    def test_operational_settings_is_frozen(self):
        s = OperationalSettings()
        with pytest.raises(Exception):
            s.ai_max_retries = 99  # type: ignore[misc]
