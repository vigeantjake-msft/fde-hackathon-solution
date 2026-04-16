"""Shared pytest fixtures for the sample app test suite."""

import os

import pytest
from fastapi.testclient import TestClient

# Provide required env vars before any app module is imported so
# settings.py does not raise ConfigurationError during collection.
os.environ.setdefault("AZURE_OPENAI_ENDPOINT", "https://test.example.com/")
os.environ.setdefault("TRIAGE_MODEL", "gpt-test")
os.environ.setdefault("EXTRACT_MODEL", "gpt-test")
os.environ.setdefault("ORCHESTRATE_MODEL", "gpt-test")

from main import app  # noqa: E402


@pytest.fixture
def client() -> TestClient:
    """Synchronous HTTPX test client — no real network calls required."""
    return TestClient(app, raise_server_exceptions=False)
