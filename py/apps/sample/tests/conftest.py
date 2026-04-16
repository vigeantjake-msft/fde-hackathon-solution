"""Shared pytest fixtures for the sample app test suite."""

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client() -> TestClient:
    """Synchronous HTTPX test client — no real network calls required."""
    return TestClient(app, raise_server_exceptions=False)
