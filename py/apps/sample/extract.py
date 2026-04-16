"""Task 2 — Document Extraction.

Uses gpt-4o vision to extract structured data from base64-encoded
document images (receipts, invoices, forms, financial statements).
The output schema is provided per-document as a JSON string.

Scoring dimensions:
  information_accuracy  recursive field F1 with value normalisation  (70%)
  text_fidelity         exact match after normalisation               (30%)

Public interface: run_extract(req, client) -> ExtractResponse
"""

import json
import logging
from typing import Any

from models import ExtractRequest
from models import ExtractResponse
from openai import AsyncAzureOpenAI
from settings import settings
from utils import chat_with_retry
from utils import detect_media_type
from utils import extract_json

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = (
    "You are a precise document data extraction AI. "
    "Extract structured data from document images exactly as shown. "
    "Numbers: omit currency symbols and commas (1234.56 not $1,234.56). "
    "Booleans: true or false. "
    "Missing or illegible fields: null. "
    "Respond with ONLY a valid JSON object — no markdown, no explanation."
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_schema_instruction(json_schema: str | None) -> str:
    """Convert the per-document schema string into a model instruction.

    Pretty-prints the schema JSON when valid; falls back to including the
    raw string when parsing fails.

    Args:
        json_schema: Raw JSON schema string from the extraction request,
                     or None if no schema was provided.

    Returns:
        A multi-line instruction string, or "" if no schema was given.
    """
    if not json_schema:
        return ""
    try:
        schema_obj = json.loads(json_schema)
        return (
            "\n\nExtract ALL fields per this JSON schema:\n"
            f"{json.dumps(schema_obj, indent=2)}"
        )
    except json.JSONDecodeError:
        return f"\n\nExtract fields described by: {json_schema}"


def _build_user_message(data_url: str, schema_instruction: str) -> dict[str, Any]:
    """Construct the multipart user message for the vision call.

    Uses detail="high" to give gpt-4o the most pixels to work with,
    which matters for dense documents such as scanned receipts.

    Args:
        data_url: A data:{mime};base64,{content} URI.
        schema_instruction: The schema hint from _build_schema_instruction.

    Returns:
        A dict in the {"role": "user", "content": [...]} format.
    """
    return {
        "role": "user",
        "content": [
            {
                "type": "image_url",
                "image_url": {"url": data_url, "detail": "high"},
            },
            {
                "type": "text",
                "text": (
                    f"Extract all data from this document."
                    f"{schema_instruction}\n\nReturn ONLY valid JSON."
                ),
            },
        ],
    }


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


async def run_extract(req: ExtractRequest, client: AsyncAzureOpenAI) -> ExtractResponse:
    """Extract structured fields from a document image.

    Detects the image format from the base64 header bytes, constructs a
    multipart vision message, and makes one LLM call (with retries).
    Dynamic fields returned by the model are merged into an ExtractResponse
    via model_config = ConfigDict(extra="allow").

    Args:
        req: Validated extraction request (base64 image + JSON schema).
        client: An AsyncAzureOpenAI instance.

    Returns:
        ExtractResponse with document_id plus all extracted fields.
        Returns ExtractResponse(document_id=req.document_id) with no
        additional fields if the model response cannot be parsed.

    Raises:
        LLMError: If the LLM call fails after all retries.
    """
    media_type = detect_media_type(req.content)
    data_url = f"data:{media_type};base64,{req.content}"
    schema_instruction = _build_schema_instruction(req.json_schema)

    resp = await chat_with_retry(
        client,
        model=settings.azure.extract_deployment,
        max_completion_tokens=4096,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            _build_user_message(data_url, schema_instruction),
        ],
    )

    raw = resp.choices[0].message.content or ""
    try:
        data = extract_json(raw)
    except Exception:
        logger.warning("extract_parse_failed doc=%s preview=%r", req.document_id, raw[:200])
        data = {}

    return ExtractResponse(document_id=req.document_id, **data)
