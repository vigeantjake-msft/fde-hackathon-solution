"""FDEBench solution — FastAPI application entry point.

Intentionally thin: HTTP routing, exception handling, and the model-name
response header.  All AI logic lives in the task modules.

Run:
    cd py && make run     # start on :8000
    cd py && make eval    # score all 3 tasks (second terminal)
"""

import logging

from client import get_client
from exceptions import FDEBenchError
from extract import run_extract
from fastapi import FastAPI
from fastapi import Request
from fastapi import Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from models import ExtractRequest
from models import ExtractResponse
from models import OrchestrateRequest
from models import OrchestrateResponse
from models import TriageRequest
from models import TriageResponse
from orchestrate import run_orchestrate
from settings import settings
from triage import run_triage

logger = logging.getLogger(__name__)

app = FastAPI(title="FDEBench Solution", version="1.0.0")


# ── Exception handlers ───────────────────────────────────────────────────────


@app.exception_handler(RequestValidationError)
async def _on_validation_error(
    _request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Return 422 for malformed or schema-invalid request bodies."""
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(FDEBenchError)
async def _on_app_error(
    _request: Request,
    exc: FDEBenchError,
) -> JSONResponse:
    """Map domain exceptions to their declared HTTP status codes."""
    logger.error("app_error type=%s message=%s", type(exc).__name__, exc.message)
    return JSONResponse(status_code=exc.http_status, content={"detail": exc.message})


@app.exception_handler(Exception)
async def _on_unexpected_error(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Catch-all for unhandled exceptions — log full traceback, return 500."""
    logger.exception("unhandled_error path=%s", request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# ── Response header ──────────────────────────────────────────────────────────


def _set_model_header(response: Response) -> None:
    """Set the X-Model-Name header required by FDEBench cost-tier scoring."""
    response.headers["X-Model-Name"] = settings.scoring.model_header


# ── Routes ───────────────────────────────────────────────────────────────────


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/triage")
async def triage(req: TriageRequest, response: Response) -> TriageResponse:
    _set_model_header(response)
    return await run_triage(req, get_client())


@app.post("/extract")
async def extract(req: ExtractRequest, response: Response) -> ExtractResponse:
    _set_model_header(response)
    return await run_extract(req, get_client())


@app.post("/orchestrate")
async def orchestrate(req: OrchestrateRequest, response: Response) -> OrchestrateResponse:
    _set_model_header(response)
    return await run_orchestrate(req, get_client())
