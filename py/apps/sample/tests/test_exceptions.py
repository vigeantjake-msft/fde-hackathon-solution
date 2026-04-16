"""Tests for exceptions.py — hierarchy and http_status attributes."""

import pytest

from exceptions import ConfigurationError
from exceptions import ExtractError
from exceptions import FDEBenchError
from exceptions import LLMError
from exceptions import LLMResponseParseError
from exceptions import OrchestrateError
from exceptions import ToolCallError
from exceptions import TriageError


class TestFDEBenchErrorHierarchy:
    """All domain exceptions inherit from FDEBenchError."""

    def test_llm_error_is_fdebench_error(self):
        assert issubclass(LLMError, FDEBenchError)

    def test_llm_response_parse_error_is_fdebench_error(self):
        assert issubclass(LLMResponseParseError, FDEBenchError)

    def test_tool_call_error_is_fdebench_error(self):
        assert issubclass(ToolCallError, FDEBenchError)

    def test_triage_error_is_fdebench_error(self):
        assert issubclass(TriageError, FDEBenchError)

    def test_extract_error_is_fdebench_error(self):
        assert issubclass(ExtractError, FDEBenchError)

    def test_orchestrate_error_is_fdebench_error(self):
        assert issubclass(OrchestrateError, FDEBenchError)

    def test_configuration_error_is_fdebench_error(self):
        assert issubclass(ConfigurationError, FDEBenchError)

    def test_fdebench_error_is_base_exception(self):
        assert issubclass(FDEBenchError, Exception)


class TestHttpStatusCodes:
    """Each exception type declares the correct HTTP status for its route handler."""

    def test_fdebench_error_default_status_is_500(self):
        assert FDEBenchError.http_status == 500

    def test_llm_error_is_502_bad_gateway(self):
        # The LLM is an upstream dependency — 502 is correct when it fails.
        assert LLMError.http_status == 502

    def test_llm_response_parse_error_is_502(self):
        assert LLMResponseParseError.http_status == 502

    def test_tool_call_error_is_502(self):
        assert ToolCallError.http_status == 502


class TestExceptionConstruction:
    """Exceptions carry their message and expose it via .message."""

    def test_message_attribute_set_on_init(self):
        exc = FDEBenchError("something went wrong")
        assert exc.message == "something went wrong"

    def test_str_representation_is_message(self):
        exc = LLMError("upstream timeout")
        assert str(exc) == "upstream timeout"

    def test_can_catch_by_base_class(self):
        with pytest.raises(FDEBenchError):
            raise LLMError("boom")

    def test_can_catch_by_specific_class(self):
        with pytest.raises(LLMError):
            raise LLMError("boom")

    def test_does_not_catch_wrong_subclass(self):
        # TriageError must not be caught as LLMError — they are siblings.
        with pytest.raises(TriageError):
            raise TriageError("triage failed")
