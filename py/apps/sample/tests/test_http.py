"""HTTP-layer tests — routes, error handlers, resilience probes.

Uses FastAPI's TestClient (synchronous HTTPX) so no real Azure calls are made.
Task functions are patched at the route level so each test is fully isolated.
"""

import json
from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from models import Category
from models import OrchestrateResponse
from models import StepExecuted
from models import Team
from models import TriageResponse


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


VALID_TRIAGE_PAYLOAD = {
    "ticket_id": "SIG-0001",
    "subject": "Subspace relay fragmentation",
    "description": "Long-range transmissions fragmenting since 0600.",
    "reporter": {
        "name": "Sarah Chen",
        "email": "sarah.chen@cdss.space",
        "department": "Engineering",
    },
    "created_at": "2026-01-01T00:00:00Z",
    "channel": "bridge_terminal",
    "attachments": [],
}

VALID_TRIAGE_RESPONSE = TriageResponse(
    ticket_id="SIG-0001",
    category=Category.COMMS,
    priority="P3",
    assigned_team=Team.COMMS,
    needs_escalation=False,
    missing_information=[],
    next_best_action="Check the relay.",
    remediation_steps=["Step 1", "Step 2"],
)

VALID_ORCHESTRATE_RESPONSE = OrchestrateResponse(
    task_id="TASK-0001",
    status="completed",
    steps_executed=[
        StepExecuted(step=1, tool="crm_search", parameters={"filter": "active"}, success=True)
    ],
    constraints_satisfied=["High-risk accounts go to retention team"],
)


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------


class TestHealth:
    def test_health_returns_200(self, client: TestClient):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_returns_ok_status(self, client: TestClient):
        resp = client.get("/health")
        assert resp.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# /triage — happy path and resilience probes
# ---------------------------------------------------------------------------


class TestTriageHappyPath:
    def test_returns_200_with_valid_payload(self, client: TestClient):
        with patch("main.run_triage", new_callable=AsyncMock) as mock_triage:
            mock_triage.return_value = VALID_TRIAGE_RESPONSE
            resp = client.post("/triage", json=VALID_TRIAGE_PAYLOAD)

        assert resp.status_code == 200

    def test_response_contains_ticket_id(self, client: TestClient):
        with patch("main.run_triage", new_callable=AsyncMock) as mock_triage:
            mock_triage.return_value = VALID_TRIAGE_RESPONSE
            resp = client.post("/triage", json=VALID_TRIAGE_PAYLOAD)

        assert resp.json()["ticket_id"] == "SIG-0001"

    def test_x_model_name_header_present(self, client: TestClient):
        with patch("main.run_triage", new_callable=AsyncMock) as mock_triage:
            mock_triage.return_value = VALID_TRIAGE_RESPONSE
            resp = client.post("/triage", json=VALID_TRIAGE_PAYLOAD)

        assert "X-Model-Name" in resp.headers

    def test_x_model_name_header_is_non_empty(self, client: TestClient):
        with patch("main.run_triage", new_callable=AsyncMock) as mock_triage:
            mock_triage.return_value = VALID_TRIAGE_RESPONSE
            resp = client.post("/triage", json=VALID_TRIAGE_PAYLOAD)

        assert resp.headers["X-Model-Name"] != ""


class TestTriageResilienceProbes:
    """Mirroring the 7 FDEBench API resilience probes."""

    def test_malformed_json_returns_4xx(self, client: TestClient):
        resp = client.post("/triage", content="not json {{", headers={"Content-Type": "application/json"})
        assert resp.status_code in (400, 422)

    def test_empty_body_returns_4xx(self, client: TestClient):
        resp = client.post("/triage", content="", headers={"Content-Type": "application/json"})
        assert resp.status_code in (400, 422)

    def test_missing_required_fields_returns_4xx(self, client: TestClient):
        resp = client.post("/triage", json={"ticket_id": "SIG-0001"})
        assert resp.status_code in (400, 422)

    def test_missing_nested_reporter_returns_4xx(self, client: TestClient):
        payload = dict(VALID_TRIAGE_PAYLOAD)
        del payload["reporter"]
        resp = client.post("/triage", json=payload)
        assert resp.status_code in (400, 422)

    def test_invalid_channel_value_returns_4xx(self, client: TestClient):
        payload = {**VALID_TRIAGE_PAYLOAD, "channel": "not_a_real_channel"}
        resp = client.post("/triage", json=payload)
        assert resp.status_code in (400, 422)

    def test_wrong_content_type_still_handled(self, client: TestClient):
        # FastAPI either accepts the request or returns a clean non-500 error.
        resp = client.post("/triage", data="text body", headers={"Content-Type": "text/plain"})
        assert resp.status_code != 500

    def test_unexpected_extra_fields_are_accepted(self, client: TestClient):
        """Extra fields should not cause a 4xx — Pydantic ignores them by default."""
        payload = {**VALID_TRIAGE_PAYLOAD, "unknown_field": "ignored"}
        with patch("main.run_triage", new_callable=AsyncMock) as mock_triage:
            mock_triage.return_value = VALID_TRIAGE_RESPONSE
            resp = client.post("/triage", json=payload)
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# /extract — happy path and resilience probes
# ---------------------------------------------------------------------------


MINIMAL_PNG_B64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

VALID_EXTRACT_PAYLOAD = {
    "document_id": "DOC-001",
    "content": MINIMAL_PNG_B64,
    "content_format": "image_base64",
    "json_schema": json.dumps({"properties": {"vendor": {"type": "string"}}}),
}


class TestExtractHappyPath:
    def test_returns_200_with_valid_payload(self, client: TestClient):
        from models import ExtractResponse

        with patch("main.run_extract", new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = ExtractResponse(document_id="DOC-001")
            resp = client.post("/extract", json=VALID_EXTRACT_PAYLOAD)

        assert resp.status_code == 200

    def test_response_contains_document_id(self, client: TestClient):
        from models import ExtractResponse

        with patch("main.run_extract", new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = ExtractResponse(document_id="DOC-001")
            resp = client.post("/extract", json=VALID_EXTRACT_PAYLOAD)

        assert resp.json()["document_id"] == "DOC-001"

    def test_x_model_name_header_present(self, client: TestClient):
        from models import ExtractResponse

        with patch("main.run_extract", new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = ExtractResponse(document_id="DOC-001")
            resp = client.post("/extract", json=VALID_EXTRACT_PAYLOAD)

        assert "X-Model-Name" in resp.headers


class TestExtractResilienceProbes:
    def test_missing_document_id_returns_4xx(self, client: TestClient):
        payload = {k: v for k, v in VALID_EXTRACT_PAYLOAD.items() if k != "document_id"}
        resp = client.post("/extract", json=payload)
        assert resp.status_code in (400, 422)

    def test_missing_content_returns_4xx(self, client: TestClient):
        payload = {k: v for k, v in VALID_EXTRACT_PAYLOAD.items() if k != "content"}
        resp = client.post("/extract", json=payload)
        assert resp.status_code in (400, 422)

    def test_malformed_json_returns_4xx(self, client: TestClient):
        resp = client.post("/extract", content="{bad json", headers={"Content-Type": "application/json"})
        assert resp.status_code in (400, 422)


# ---------------------------------------------------------------------------
# /orchestrate — happy path and resilience probes
# ---------------------------------------------------------------------------


VALID_ORCHESTRATE_PAYLOAD = {
    "task_id": "TASK-0001",
    "goal": "Analyse churn risk for declining-usage accounts",
    "available_tools": [
        {
            "name": "crm_search",
            "description": "Search CRM accounts",
            "endpoint": "https://tools.fdebench.dev/crm/search",
            "parameters": [
                {"name": "filter", "type": "string", "description": "filter", "required": True}
            ],
        }
    ],
    "constraints": ["High-risk accounts go to retention team"],
    "mock_service_url": "http://localhost:9090",
}


class TestOrchestrateHappyPath:
    def test_returns_200_with_valid_payload(self, client: TestClient):
        with patch("main.run_orchestrate", new_callable=AsyncMock) as mock_orch:
            mock_orch.return_value = VALID_ORCHESTRATE_RESPONSE
            resp = client.post("/orchestrate", json=VALID_ORCHESTRATE_PAYLOAD)

        assert resp.status_code == 200

    def test_response_contains_task_id(self, client: TestClient):
        with patch("main.run_orchestrate", new_callable=AsyncMock) as mock_orch:
            mock_orch.return_value = VALID_ORCHESTRATE_RESPONSE
            resp = client.post("/orchestrate", json=VALID_ORCHESTRATE_PAYLOAD)

        assert resp.json()["task_id"] == "TASK-0001"

    def test_response_contains_steps_executed(self, client: TestClient):
        with patch("main.run_orchestrate", new_callable=AsyncMock) as mock_orch:
            mock_orch.return_value = VALID_ORCHESTRATE_RESPONSE
            resp = client.post("/orchestrate", json=VALID_ORCHESTRATE_PAYLOAD)

        assert "steps_executed" in resp.json()

    def test_x_model_name_header_present(self, client: TestClient):
        with patch("main.run_orchestrate", new_callable=AsyncMock) as mock_orch:
            mock_orch.return_value = VALID_ORCHESTRATE_RESPONSE
            resp = client.post("/orchestrate", json=VALID_ORCHESTRATE_PAYLOAD)

        assert "X-Model-Name" in resp.headers


class TestOrchestrateResilienceProbes:
    def test_missing_task_id_returns_4xx(self, client: TestClient):
        payload = {k: v for k, v in VALID_ORCHESTRATE_PAYLOAD.items() if k != "task_id"}
        resp = client.post("/orchestrate", json=payload)
        assert resp.status_code in (400, 422)

    def test_missing_goal_returns_4xx(self, client: TestClient):
        payload = {k: v for k, v in VALID_ORCHESTRATE_PAYLOAD.items() if k != "goal"}
        resp = client.post("/orchestrate", json=payload)
        assert resp.status_code in (400, 422)

    def test_malformed_json_returns_4xx(self, client: TestClient):
        resp = client.post("/orchestrate", content="{{bad", headers={"Content-Type": "application/json"})
        assert resp.status_code in (400, 422)

    def test_empty_body_returns_4xx(self, client: TestClient):
        resp = client.post("/orchestrate", content="", headers={"Content-Type": "application/json"})
        assert resp.status_code in (400, 422)

    def test_mock_service_url_is_optional(self, client: TestClient):
        """mock_service_url is optional — omitting it must not cause a 4xx."""
        payload = {k: v for k, v in VALID_ORCHESTRATE_PAYLOAD.items() if k != "mock_service_url"}
        with patch("main.run_orchestrate", new_callable=AsyncMock) as mock_orch:
            mock_orch.return_value = VALID_ORCHESTRATE_RESPONSE
            resp = client.post("/orchestrate", json=payload)
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Exception handler mapping
# ---------------------------------------------------------------------------


class TestExceptionHandlers:
    def test_app_error_returns_correct_status(self, client: TestClient):
        from exceptions import LLMError

        with patch("main.run_triage", new_callable=AsyncMock) as mock_triage:
            mock_triage.side_effect = LLMError("upstream failed")
            resp = client.post("/triage", json=VALID_TRIAGE_PAYLOAD)

        # LLMError.http_status == 502
        assert resp.status_code == 502
        assert resp.json()["detail"] == "upstream failed"

    def test_unexpected_error_returns_500(self, client: TestClient):
        with patch("main.run_triage", new_callable=AsyncMock) as mock_triage:
            mock_triage.side_effect = RuntimeError("unexpected")
            resp = client.post("/triage", json=VALID_TRIAGE_PAYLOAD)

        assert resp.status_code == 500
        assert "Internal server error" in resp.json()["detail"]
