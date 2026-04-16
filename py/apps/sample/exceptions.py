"""Application exception hierarchy.

All domain errors inherit from FDEBenchError so callers can catch the
entire family or specific subtypes.  The http_status attribute lets
main.py map exceptions to appropriate HTTP responses without coupling
task logic to FastAPI.
"""


class FDEBenchError(Exception):
    """Base class for all application-level errors."""

    http_status: int = 500

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


# ---------------------------------------------------------------------------
# Infrastructure errors
# ---------------------------------------------------------------------------


class LLMError(FDEBenchError):
    """The LLM call failed after all retries were exhausted."""

    http_status = 502


class LLMResponseParseError(FDEBenchError):
    """The LLM returned a response that could not be parsed into the expected schema."""

    http_status = 502


class ToolCallError(FDEBenchError):
    """An HTTP tool call in the orchestration loop returned an unrecoverable error.

    Note: 404 responses from the mock service for action tools
    (notification_send, audit_log) are expected and should NOT raise this
    exception.  Reserve it for truly fatal failures (e.g. connection
    refused on the first lookup call).
    """

    http_status = 502


# ---------------------------------------------------------------------------
# Task-level errors
# ---------------------------------------------------------------------------


class TriageError(FDEBenchError):
    """An unrecoverable error occurred in the signal triage pipeline."""


class ExtractError(FDEBenchError):
    """An unrecoverable error occurred in the document extraction pipeline."""


class OrchestrateError(FDEBenchError):
    """An unrecoverable error occurred in the workflow orchestration pipeline."""


# ---------------------------------------------------------------------------
# Configuration errors — should surface at startup, not at request time
# ---------------------------------------------------------------------------


class ConfigurationError(FDEBenchError):
    """A required configuration value is missing or invalid.

    Raised at startup / import time so misconfiguration is caught before
    the server starts accepting requests.
    """
