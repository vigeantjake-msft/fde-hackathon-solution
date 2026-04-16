"""Tests for extract.py — schema instruction builder, vision message, run_extract."""

import base64
import json
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest

from extract import _build_schema_instruction
from extract import _build_user_message
from extract import run_extract
from models import ExtractRequest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_request(
    document_id: str = "DOC-001",
    content: str | None = None,
    json_schema: str | None = None,
) -> ExtractRequest:
    if content is None:
        # Minimal valid PNG header padded to realistic length.
        png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 20
        content = base64.b64encode(png_bytes).decode()
    return ExtractRequest(
        document_id=document_id,
        content=content,
        json_schema=json_schema,
    )


def _llm_response(content: str) -> MagicMock:
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


# ---------------------------------------------------------------------------
# _build_schema_instruction — pure function
# ---------------------------------------------------------------------------


class TestBuildSchemaInstruction:
    """_build_schema_instruction converts a JSON schema string to a model hint."""

    def test_none_returns_empty_string(self):
        assert _build_schema_instruction(None) == ""

    def test_valid_json_schema_is_pretty_printed(self):
        schema = json.dumps({"type": "object", "properties": {"name": {"type": "string"}}})
        result = _build_schema_instruction(schema)
        assert "Extract ALL fields per this JSON schema:" in result
        assert '"type": "object"' in result  # pretty-printed

    def test_invalid_json_schema_falls_back_to_raw_string(self):
        invalid = "not valid json {"
        result = _build_schema_instruction(invalid)
        assert "Extract fields described by" in result
        assert invalid in result

    def test_nested_schema_is_included(self):
        schema = json.dumps({
            "type": "object",
            "properties": {
                "address": {
                    "type": "object",
                    "properties": {"street": {"type": "string"}},
                }
            },
        })
        result = _build_schema_instruction(schema)
        assert "address" in result
        assert "street" in result


# ---------------------------------------------------------------------------
# _build_user_message — pure function
# ---------------------------------------------------------------------------


class TestBuildUserMessage:
    """_build_user_message constructs the multipart vision call."""

    def test_returns_user_role(self):
        msg = _build_user_message("data:image/png;base64,abc", "")
        assert msg["role"] == "user"

    def test_content_has_two_parts(self):
        msg = _build_user_message("data:image/png;base64,abc", "")
        assert len(msg["content"]) == 2

    def test_first_part_is_image_url(self):
        msg = _build_user_message("data:image/png;base64,abc", "")
        first = msg["content"][0]
        assert first["type"] == "image_url"
        assert first["image_url"]["url"] == "data:image/png;base64,abc"
        assert first["image_url"]["detail"] == "high"

    def test_second_part_is_text_with_extract_instruction(self):
        msg = _build_user_message("data:image/png;base64,abc", "")
        second = msg["content"][1]
        assert second["type"] == "text"
        assert "Extract all data from this document" in second["text"]

    def test_schema_instruction_is_appended_to_text(self):
        hint = "\n\nExtract ALL fields per this JSON schema:\n{}"
        msg = _build_user_message("data:image/png;base64,abc", hint)
        assert hint in msg["content"][1]["text"]

    def test_data_url_is_forwarded_verbatim(self):
        url = "data:image/jpeg;base64,/9j/4AAQ"
        msg = _build_user_message(url, "")
        assert msg["content"][0]["image_url"]["url"] == url


# ---------------------------------------------------------------------------
# run_extract — LLM call mocked
# ---------------------------------------------------------------------------


class TestRunExtract:
    """run_extract returns an ExtractResponse with document_id plus extracted fields."""

    async def test_document_id_is_echoed(self):
        client = AsyncMock()
        client.chat.completions.create.return_value = _llm_response('{"amount": 42.50}')

        result = await run_extract(_make_request(document_id="DOC-RECEIPT-001"), client)

        assert result.document_id == "DOC-RECEIPT-001"

    async def test_extracted_fields_appear_in_response(self):
        client = AsyncMock()
        client.chat.completions.create.return_value = _llm_response(
            '{"vendor": "Contoso", "total": 1234.56, "date": "2026-01-15"}'
        )

        result = await run_extract(_make_request(), client)

        assert result.model_extra["vendor"] == "Contoso"
        assert result.model_extra["total"] == 1234.56
        assert result.model_extra["date"] == "2026-01-15"

    async def test_makes_exactly_one_llm_call(self):
        client = AsyncMock()
        client.chat.completions.create.return_value = _llm_response("{}")

        await run_extract(_make_request(), client)

        client.chat.completions.create.assert_called_once()

    async def test_json_schema_is_passed_to_model(self):
        client = AsyncMock()
        client.chat.completions.create.return_value = _llm_response("{}")
        schema = json.dumps({"properties": {"name": {"type": "string"}}})

        await run_extract(_make_request(json_schema=schema), client)

        call_kwargs = client.chat.completions.create.call_args.kwargs
        user_content = call_kwargs["messages"][1]["content"]
        # The schema instruction should appear in the text block.
        text_block = next(p for p in user_content if p["type"] == "text")
        assert "name" in text_block["text"]

    async def test_uses_high_detail_vision(self):
        client = AsyncMock()
        client.chat.completions.create.return_value = _llm_response("{}")

        await run_extract(_make_request(), client)

        call_kwargs = client.chat.completions.create.call_args.kwargs
        user_content = call_kwargs["messages"][1]["content"]
        image_block = next(p for p in user_content if p["type"] == "image_url")
        assert image_block["image_url"]["detail"] == "high"

    async def test_returns_only_document_id_when_llm_returns_empty(self):
        client = AsyncMock()
        client.chat.completions.create.return_value = _llm_response("")

        result = await run_extract(_make_request(document_id="DOC-EMPTY"), client)

        assert result.document_id == "DOC-EMPTY"
        assert result.model_extra == {}

    async def test_uses_json_object_response_format(self):
        client = AsyncMock()
        client.chat.completions.create.return_value = _llm_response("{}")

        await run_extract(_make_request(), client)

        call_kwargs = client.chat.completions.create.call_args.kwargs
        assert call_kwargs["response_format"] == {"type": "json_object"}

    async def test_propagates_llm_error_after_retries(self):
        from exceptions import LLMError

        client = AsyncMock()
        client.chat.completions.create.side_effect = RuntimeError("Azure error")

        import asyncio
        from unittest.mock import patch

        with patch.object(asyncio, "sleep", new_callable=AsyncMock):
            with pytest.raises(LLMError):
                await run_extract(_make_request(), client)
