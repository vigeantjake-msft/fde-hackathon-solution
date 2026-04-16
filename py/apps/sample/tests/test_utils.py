"""Tests for utils.py — extract_json, detect_media_type, chat_with_retry."""

import base64
import json
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest

from exceptions import LLMError
from utils import chat_with_retry
from utils import detect_media_type
from utils import extract_json


class TestExtractJson:
    """extract_json parses JSON from LLM text using three fallback strategies."""

    def test_direct_parse_clean_json(self):
        raw = '{"category": "Crew Access & Biometrics", "priority": "P2"}'
        result = extract_json(raw)
        assert result == {"category": "Crew Access & Biometrics", "priority": "P2"}

    def test_direct_parse_strips_surrounding_whitespace(self):
        raw = '\n  {"key": "value"}  \n'
        assert extract_json(raw) == {"key": "value"}

    def test_code_fence_json_block(self):
        raw = '```json\n{"category": "Hull & Structural Systems"}\n```'
        assert extract_json(raw) == {"category": "Hull & Structural Systems"}

    def test_code_fence_without_language_tag(self):
        raw = '```\n{"priority": "P1"}\n```'
        assert extract_json(raw) == {"priority": "P1"}

    def test_brace_scan_strips_surrounding_prose(self):
        raw = 'Here is the result: {"status": "completed"} — done.'
        assert extract_json(raw) == {"status": "completed"}

    def test_nested_object(self):
        raw = '{"reporter": {"name": "Alice", "department": "Ops"}, "priority": "P3"}'
        result = extract_json(raw)
        assert result["reporter"]["name"] == "Alice"

    def test_empty_object(self):
        assert extract_json("{}") == {}

    def test_returns_empty_dict_on_total_failure(self):
        assert extract_json("this is not JSON at all") == {}

    def test_returns_empty_dict_on_empty_string(self):
        assert extract_json("") == {}

    def test_returns_empty_dict_on_partial_json(self):
        assert extract_json('{"key": ') == {}

    def test_code_fence_with_invalid_inner_json_falls_through_to_brace_scan(self):
        # Code fence content is invalid, but there's a valid JSON object after it.
        raw = '```json\nnot valid\n```\nactual: {"key": "value"}'
        result = extract_json(raw)
        assert result == {"key": "value"}

    def test_multiline_remediation_steps(self):
        raw = json.dumps({"remediation_steps": ["Step 1", "Step 2", "Step 3"]})
        result = extract_json(raw)
        assert result["remediation_steps"] == ["Step 1", "Step 2", "Step 3"]


class TestDetectMediaType:
    """detect_media_type sniffs MIME type from base64 content header bytes."""

    def _encode(self, header_bytes: bytes) -> str:
        # Pad to make a realistic base64 chunk (at least 24 chars).
        return base64.b64encode(header_bytes + b"\x00" * 20).decode()

    def test_png_magic_bytes(self):
        png_header = b"\x89PNG\r\n\x1a\n" + b"\x00" * 8
        b64 = self._encode(png_header)
        assert detect_media_type(b64) == "image/png"

    def test_jpeg_magic_bytes(self):
        jpeg_header = b"\xff\xd8\xff\xe0" + b"\x00" * 12
        b64 = self._encode(jpeg_header)
        assert detect_media_type(b64) == "image/jpeg"

    def test_gif87a_magic_bytes(self):
        gif_header = b"GIF87a" + b"\x00" * 10
        b64 = self._encode(gif_header)
        assert detect_media_type(b64) == "image/gif"

    def test_gif89a_magic_bytes(self):
        gif_header = b"GIF89a" + b"\x00" * 10
        b64 = self._encode(gif_header)
        assert detect_media_type(b64) == "image/gif"

    def test_unknown_format_falls_back_to_png(self):
        unknown = b"\x00\x01\x02\x03" + b"\x00" * 12
        b64 = self._encode(unknown)
        assert detect_media_type(b64) == "image/png"

    def test_empty_string_falls_back_to_png(self):
        assert detect_media_type("") == "image/png"

    def test_invalid_base64_falls_back_to_png(self):
        assert detect_media_type("!!!not_base64!!!") == "image/png"


class TestChatWithRetry:
    """chat_with_retry wraps the Azure OpenAI call with exponential backoff."""

    async def test_returns_response_on_first_success(self):
        client = AsyncMock()
        expected = MagicMock()
        client.chat.completions.create.return_value = expected

        result = await chat_with_retry(client, model="gpt-5.4", messages=[])

        assert result is expected
        client.chat.completions.create.assert_called_once_with(model="gpt-5.4", messages=[])

    async def test_retries_on_transient_error_then_succeeds(self):
        client = AsyncMock()
        success_response = MagicMock()
        client.chat.completions.create.side_effect = [
            RuntimeError("transient"),
            success_response,
        ]

        # Patch asyncio.sleep so tests don't actually wait.
        import asyncio
        from unittest.mock import patch

        with patch.object(asyncio, "sleep", new_callable=AsyncMock):
            result = await chat_with_retry(client, model="gpt-5.4", messages=[])

        assert result is success_response
        assert client.chat.completions.create.call_count == 2

    async def test_raises_llm_error_after_all_retries_exhausted(self):
        client = AsyncMock()
        client.chat.completions.create.side_effect = RuntimeError("always fails")

        import asyncio
        from unittest.mock import patch

        with patch.object(asyncio, "sleep", new_callable=AsyncMock):
            with pytest.raises(LLMError, match="LLM call failed after"):
                await chat_with_retry(client, model="gpt-5.4", messages=[])

    async def test_forwards_all_kwargs_to_create(self):
        client = AsyncMock()
        client.chat.completions.create.return_value = MagicMock()

        await chat_with_retry(
            client,
            model="gpt-5.4",
            max_tokens=512,
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": "hi"}],
        )

        client.chat.completions.create.assert_called_once_with(
            model="gpt-5.4",
            max_tokens=512,
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": "hi"}],
        )
