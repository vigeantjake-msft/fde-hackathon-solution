"""Tests for settings.py — default values and env-var overrides."""

import os
from unittest.mock import patch

from settings import AzureSettings
from settings import OperationalSettings
from settings import ScoringSettings
from settings import Settings


class TestAzureSettingsDefaults:
    """Azure settings fall back to sensible defaults when no env vars are set."""

    def test_default_endpoint(self):
        s = AzureSettings()
        assert s.endpoint == "https://foundry-scus6r6osf.cognitiveservices.azure.com/"

    def test_default_api_version(self):
        s = AzureSettings()
        assert s.api_version == "2025-01-01-preview"

    def test_default_deployment(self):
        s = AzureSettings()
        assert s.deployment == "gpt-5.4"


class TestAzureSettingsEnvOverrides:
    """Azure settings read from environment variables when present."""

    def test_endpoint_override(self):
        with patch.dict(os.environ, {"AZURE_OPENAI_ENDPOINT": "https://custom.azure.com/"}):
            s = AzureSettings()
            assert s.endpoint == "https://custom.azure.com/"

    def test_deployment_override(self):
        with patch.dict(os.environ, {"AZURE_OPENAI_DEPLOYMENT": "gpt-4.1"}):
            s = AzureSettings()
            assert s.deployment == "gpt-4.1"

    def test_api_version_override(self):
        with patch.dict(os.environ, {"AZURE_OPENAI_API_VERSION": "2024-02-01"}):
            s = AzureSettings()
            assert s.api_version == "2024-02-01"


class TestScoringSettingsDefaults:
    def test_default_model_header(self):
        s = ScoringSettings()
        assert s.model_header == "gpt-5.4"

    def test_model_header_override(self):
        with patch.dict(os.environ, {"MODEL_HEADER": "gpt-4.1-mini"}):
            s = ScoringSettings()
            assert s.model_header == "gpt-4.1-mini"


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

    def test_max_retries_override(self):
        with patch.dict(os.environ, {"AI_MAX_RETRIES": "5"}):
            s = OperationalSettings()
            assert s.ai_max_retries == 5

    def test_max_turns_override(self):
        with patch.dict(os.environ, {"ORCHESTRATE_MAX_TURNS": "20"}):
            s = OperationalSettings()
            assert s.orchestrate_max_turns == 20


class TestSettingsIsFrozen:
    """Settings objects are frozen — mutation should raise."""

    def test_azure_settings_is_frozen(self):
        import pytest
        s = AzureSettings()
        with pytest.raises(Exception):
            s.deployment = "other-model"  # type: ignore[misc]

    def test_top_level_settings_is_frozen(self):
        import pytest
        s = Settings()
        with pytest.raises(Exception):
            s.azure = AzureSettings()  # type: ignore[misc]
