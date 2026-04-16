"""Shared infrastructure utilities used across all task modules.

Contains no business logic — only retry wiring, JSON extraction, and
image-format detection.  Each function is independently unit-testable
with no network or Azure dependencies.
"""

import asyncio
import base64
import json
import logging
import re
from typing import Any

from exceptions import LLMError
from openai import AsyncAzureOpenAI
from settings import settings

logger = logging.getLogger(__name__)


async def chat_with_retry(
    client: AsyncAzureOpenAI,
    **kwargs: Any,
) -> Any:
    """Call chat.completions.create with exponential-backoff retries.

    Uses settings.ops.ai_max_retries for the attempt budget.
    Waits 2**attempt seconds between retries.
    Re-raises the last exception wrapped in LLMError once exhausted.

    Args:
        client: An AsyncAzureOpenAI instance.
        **kwargs: Forwarded verbatim to chat.completions.create().

    Returns:
        The ChatCompletion response on success.

    Raises:
        LLMError: If every attempt fails.
    """
    max_retries = settings.ops.ai_max_retries
    last_exc: Exception | None = None

    for attempt in range(max_retries):
        try:
            return await client.chat.completions.create(**kwargs)
        except Exception as exc:
            last_exc = exc
            if attempt == max_retries - 1:
                break
            wait = 2**attempt
            logger.warning(
                "azure_openai_retry attempt=%d/%d error=%s wait_s=%d",
                attempt + 1,
                max_retries,
                exc,
                wait,
            )
            await asyncio.sleep(wait)

    raise LLMError(f"LLM call failed after {max_retries} attempts: {last_exc}") from last_exc


def extract_json(text: str) -> dict[str, Any]:
    """Extract a JSON object from an LLM text response.

    Tries three strategies in order:
    1. Direct json.loads on the stripped text.
    2. Extract from a markdown code fence.
    3. Scan for the first { / last } pair and parse that slice.

    Returns an empty dict on total failure rather than raising, so
    callers can apply graceful field-level defaults.

    Args:
        text: Raw text from an LLM message content field.

    Returns:
        Parsed JSON object, or {} if all strategies fail.
    """
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            pass

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass

    logger.warning("extract_json_failed preview=%r", text[:120])
    return {}


def detect_media_type(b64_content: str) -> str:
    """Detect image MIME type by sniffing the first bytes of base64 content.

    Checks PNG, JPEG, and GIF magic bytes.  Falls back to image/png
    when the content cannot be decoded or the format is unrecognised
    (gpt-4o handles PNG most reliably, so it is the safest default).

    Args:
        b64_content: Raw base64-encoded image data (no data-URI prefix).

    Returns:
        A MIME type string, e.g. "image/png".
    """
    try:
        chunk = b64_content[:24].rstrip("=")
        padding = (4 - len(chunk) % 4) % 4
        header = base64.b64decode(chunk + "=" * padding, validate=False)[:8]

        if header[:8] == b"\x89PNG\r\n\x1a\n":
            return "image/png"
        if header[:3] == b"\xff\xd8\xff":
            return "image/jpeg"
        if header[:6] in (b"GIF87a", b"GIF89a"):
            return "image/gif"
    except Exception:
        pass

    return "image/png"
