"""Tests for orchestrate.py — hint mapper, tool builder, HTTP executor, agentic loop."""

import json
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from models import OrchestrateRequest
from models import ToolDefinition
from models import ToolParameter
from orchestrate import _FINISH_TOOL_NAME
from orchestrate import _assistant_message
from orchestrate import _tool_result
from orchestrate import build_openai_tools
from orchestrate import call_tool
from orchestrate import hint_for_constraint
from orchestrate import run_orchestrate


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _tool_def(
    name: str = "crm_search",
    description: str = "Search CRM accounts",
    params: list[dict] | None = None,
) -> ToolDefinition:
    if params is None:
        params = [{"name": "filter", "type": "string", "description": "Filter expression", "required": True}]
    return ToolDefinition(
        name=name,
        description=description,
        endpoint=f"https://tools.fdebench.dev/{name}",
        parameters=[ToolParameter(**p) for p in params],
    )


def _make_request(
    task_id: str = "TASK-0001",
    goal: str = "Analyse churn risk",
    constraints: list[str] | None = None,
    tools: list[ToolDefinition] | None = None,
) -> OrchestrateRequest:
    return OrchestrateRequest(
        task_id=task_id,
        goal=goal,
        available_tools=tools or [_tool_def()],
        constraints=constraints or ["High-risk accounts go to retention team"],
        mock_service_url="http://localhost:9090",
    )


def _choice(content: str | None = None, tool_calls: list | None = None, finish_reason: str = "tool_calls") -> MagicMock:
    msg = MagicMock()
    msg.content = content
    msg.tool_calls = tool_calls or []
    choice = MagicMock()
    choice.message = msg
    choice.finish_reason = finish_reason
    return choice


def _tool_call(fn_name: str, fn_args: dict, call_id: str = "tc_001") -> MagicMock:
    fn = MagicMock()
    fn.name = fn_name
    fn.arguments = json.dumps(fn_args)
    tc = MagicMock()
    tc.id = call_id
    tc.function = fn
    return tc


def _finish_call(status: str = "completed", satisfied: list[str] | None = None) -> MagicMock:
    return _tool_call(
        _FINISH_TOOL_NAME,
        {"status": status, "constraints_satisfied": satisfied or []},
        call_id="tc_finish",
    )


def _ai_response(*choices) -> MagicMock:
    resp = MagicMock()
    resp.choices = list(choices)
    return resp


# ---------------------------------------------------------------------------
# hint_for_constraint — pure function
# ---------------------------------------------------------------------------


class TestHintForConstraint:
    """hint_for_constraint maps constraint text to exact user_id action hints."""

    @pytest.mark.parametrize("constraint,expected_user_id", [
        ("High-risk accounts go to retention team", "lead_retention"),
        ("Route medium-risk to customer success team", "lead_customer_success"),
        ("Notify finance approver for discounts", "finance_approver"),
        ("Discount approval required for enterprise", "finance_approver"),
        ("Alert on-call engineer via SMS", "oncall_engineer"),
        ("Escalate to engineering manager", "engineering_manager"),
        ("Notify sales team of new lead", "sales_team"),
    ])
    def test_known_keywords_return_correct_user_id(self, constraint: str, expected_user_id: str):
        hint = hint_for_constraint(constraint)
        assert expected_user_id in hint

    def test_audit_log_keyword(self):
        hint = hint_for_constraint("Log all escalations to the audit trail")
        assert "audit_log" in hint

    def test_unknown_constraint_returns_empty_string(self):
        assert hint_for_constraint("Process only active accounts") == ""

    def test_matching_is_case_insensitive(self):
        hint_lower = hint_for_constraint("retention team route")
        hint_upper = hint_for_constraint("RETENTION TEAM ROUTE")
        assert hint_lower == hint_upper
        assert hint_lower != ""

    def test_first_match_wins(self):
        # "audit" appears before "log" in the table; "log" also appears in "audit"
        hint = hint_for_constraint("Log escalations")
        assert "audit_log" in hint

    def test_partial_word_match(self):
        # "customer success" contains "customer success" substring
        assert "lead_customer_success" in hint_for_constraint("route to customer success team")


# ---------------------------------------------------------------------------
# build_openai_tools — pure function
# ---------------------------------------------------------------------------


class TestBuildOpenaiTools:
    """build_openai_tools converts ToolDefinition objects to OpenAI function schema."""

    def test_returns_list_with_finish_tool_appended(self):
        tools = build_openai_tools([_tool_def()])
        assert tools[-1]["function"]["name"] == _FINISH_TOOL_NAME

    def test_tool_count_is_input_plus_one(self):
        input_tools = [_tool_def("crm_search"), _tool_def("subscription_check")]
        tools = build_openai_tools(input_tools)
        assert len(tools) == 3  # 2 + finish_workflow

    def test_tool_name_preserved(self):
        tools = build_openai_tools([_tool_def("crm_search")])
        assert tools[0]["function"]["name"] == "crm_search"

    def test_tool_description_preserved(self):
        tools = build_openai_tools([_tool_def(description="Search CRM by filter")])
        assert tools[0]["function"]["description"] == "Search CRM by filter"

    def test_required_parameter_added_to_required_list(self):
        tool = _tool_def(params=[
            {"name": "filter", "type": "string", "description": "filter", "required": True},
        ])
        tools = build_openai_tools([tool])
        required = tools[0]["function"]["parameters"]["required"]
        assert "filter" in required

    def test_optional_parameter_not_in_required_list(self):
        tool = _tool_def(params=[
            {"name": "limit", "type": "int", "description": "max results", "required": False},
        ])
        tools = build_openai_tools([tool])
        required = tools[0]["function"]["parameters"]["required"]
        assert "limit" not in required

    @pytest.mark.parametrize("task_type,expected_json_type", [
        ("int", "number"),
        ("integer", "number"),
        ("float", "number"),
        ("bool", "boolean"),
        ("boolean", "boolean"),
        ("object", "object"),
        ("dict", "object"),
        ("array", "array"),
        ("list", "array"),
        ("string", "string"),
        ("unknown_type", "string"),  # fallback
    ])
    def test_type_mapping(self, task_type: str, expected_json_type: str):
        tool = _tool_def(params=[
            {"name": "param", "type": task_type, "description": "test", "required": False},
        ])
        tools = build_openai_tools([tool])
        param_schema = tools[0]["function"]["parameters"]["properties"]["param"]
        assert param_schema["type"] == expected_json_type

    def test_finish_workflow_has_status_and_constraints_fields(self):
        tools = build_openai_tools([])
        finish = tools[-1]["function"]
        props = finish["parameters"]["properties"]
        assert "status" in props
        assert "constraints_satisfied" in props

    def test_finish_workflow_status_enum(self):
        tools = build_openai_tools([])
        status_prop = tools[-1]["function"]["parameters"]["properties"]["status"]
        assert set(status_prop["enum"]) == {"completed", "partial", "failed"}

    def test_empty_tool_list_still_has_finish_tool(self):
        tools = build_openai_tools([])
        assert len(tools) == 1
        assert tools[0]["function"]["name"] == _FINISH_TOOL_NAME


# ---------------------------------------------------------------------------
# _assistant_message and _tool_result — pure helpers
# ---------------------------------------------------------------------------


class TestConversationHelpers:
    def test_assistant_message_role_is_assistant(self):
        choice = _choice(content="hello", tool_calls=[])
        msg = _assistant_message(choice)
        assert msg["role"] == "assistant"

    def test_assistant_message_content_forwarded(self):
        choice = _choice(content="some text", tool_calls=[])
        msg = _assistant_message(choice)
        assert msg["content"] == "some text"

    def test_assistant_message_includes_tool_calls_when_present(self):
        tc = _tool_call("crm_search", {"filter": "active"})
        choice = _choice(tool_calls=[tc])
        msg = _assistant_message(choice)
        assert "tool_calls" in msg
        assert msg["tool_calls"][0]["id"] == "tc_001"
        assert msg["tool_calls"][0]["function"]["name"] == "crm_search"

    def test_assistant_message_no_tool_calls_key_when_empty(self):
        choice = _choice(content="done", tool_calls=[])
        msg = _assistant_message(choice)
        assert "tool_calls" not in msg

    def test_tool_result_role_is_tool(self):
        record = _tool_result("tc_001", {"accounts": []})
        assert record["role"] == "tool"

    def test_tool_result_id_forwarded(self):
        record = _tool_result("tc_XYZ", {"result": "ok"})
        assert record["tool_call_id"] == "tc_XYZ"

    def test_tool_result_content_is_json_string(self):
        payload = {"account_id": "ACC-001", "status": "active"}
        record = _tool_result("tc_001", payload)
        parsed = json.loads(record["content"])
        assert parsed == payload


# ---------------------------------------------------------------------------
# call_tool — HTTP executor
# ---------------------------------------------------------------------------


class TestCallTool:
    """call_tool makes POST requests to the mock service and handles errors gracefully."""

    async def test_returns_json_on_200(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"accounts": [{"id": "ACC-001"}]}

        http_client = AsyncMock()
        http_client.post.return_value = mock_resp

        result = await call_tool("http://localhost:9090", "TASK-001", "crm_search", {"filter": "active"}, http_client)

        assert result == {"accounts": [{"id": "ACC-001"}]}

    async def test_posts_to_correct_url(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {}

        http_client = AsyncMock()
        http_client.post.return_value = mock_resp

        await call_tool("http://localhost:9090", "TASK-001", "crm_search", {}, http_client)

        http_client.post.assert_called_once()
        call_url = http_client.post.call_args.args[0]
        assert call_url == "http://localhost:9090/scenario/TASK-001/crm_search"

    async def test_returns_error_dict_on_404(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.text = '{"error": "No mock for tool"}'

        http_client = AsyncMock()
        http_client.post.return_value = mock_resp

        result = await call_tool("http://localhost:9090", "TASK-001", "notification_send", {}, http_client)

        assert "error" in result
        assert "HTTP 404" in result["error"]

    async def test_returns_error_dict_on_connection_failure(self):
        http_client = AsyncMock()
        http_client.post.side_effect = ConnectionError("refused")

        result = await call_tool("http://localhost:9090", "TASK-001", "crm_search", {}, http_client)

        assert "error" in result

    async def test_trailing_slash_stripped_from_mock_url(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {}

        http_client = AsyncMock()
        http_client.post.return_value = mock_resp

        await call_tool("http://localhost:9090/", "TASK-001", "crm_search", {}, http_client)

        call_url = http_client.post.call_args.args[0]
        assert "//" not in call_url.replace("http://", "")


# ---------------------------------------------------------------------------
# run_orchestrate — full agentic loop
# ---------------------------------------------------------------------------


class TestRunOrchestrate:
    """run_orchestrate drives the LLM agent loop and returns an OrchestrateResponse."""

    async def test_returns_completed_status_after_finish_workflow(self):
        client = AsyncMock()
        # Turn 1: call crm_search. Turn 2: call finish_workflow.
        client.chat.completions.create.side_effect = [
            _ai_response(_choice(tool_calls=[_tool_call("crm_search", {"filter": "active"})])),
            _ai_response(_choice(tool_calls=[_finish_call("completed", ["constraint 1"])])),
        ]

        with patch("orchestrate.call_tool", new_callable=AsyncMock) as mock_ct:
            mock_ct.return_value = {"accounts": []}
            result = await run_orchestrate(_make_request(), client)

        assert result.status == "completed"

    async def test_steps_executed_contains_all_tool_calls(self):
        client = AsyncMock()
        client.chat.completions.create.side_effect = [
            _ai_response(_choice(tool_calls=[
                _tool_call("crm_search", {"filter": "active"}, "tc_1"),
                _tool_call("subscription_check", {"account_id": "ACC-001"}, "tc_2"),
            ])),
            _ai_response(_choice(tool_calls=[_finish_call()])),
        ]

        with patch("orchestrate.call_tool", new_callable=AsyncMock) as mock_ct:
            mock_ct.return_value = {}
            result = await run_orchestrate(_make_request(), client)

        assert len(result.steps_executed) == 2
        assert result.steps_executed[0].tool == "crm_search"
        assert result.steps_executed[1].tool == "subscription_check"

    async def test_steps_are_numbered_sequentially(self):
        client = AsyncMock()
        client.chat.completions.create.side_effect = [
            _ai_response(_choice(tool_calls=[
                _tool_call("crm_search", {}, "tc_1"),
                _tool_call("crm_search", {}, "tc_2"),
            ])),
            _ai_response(_choice(tool_calls=[_finish_call()])),
        ]

        with patch("orchestrate.call_tool", new_callable=AsyncMock) as mock_ct:
            mock_ct.return_value = {}
            result = await run_orchestrate(_make_request(), client)

        step_nums = [s.step for s in result.steps_executed]
        assert step_nums == [1, 2]

    async def test_constraints_satisfied_from_finish_workflow(self):
        client = AsyncMock()
        satisfied = ["High-risk accounts go to retention team", "Log all escalations"]
        client.chat.completions.create.side_effect = [
            _ai_response(_choice(tool_calls=[_finish_call("completed", satisfied)])),
        ]

        result = await run_orchestrate(_make_request(), client)

        assert result.constraints_satisfied == satisfied

    async def test_task_id_is_echoed(self):
        client = AsyncMock()
        client.chat.completions.create.return_value = _ai_response(
            _choice(tool_calls=[_finish_call()]),
        )

        result = await run_orchestrate(_make_request(task_id="TASK-9999"), client)

        assert result.task_id == "TASK-9999"

    async def test_email_send_success_increments_emails_sent(self):
        client = AsyncMock()
        client.chat.completions.create.side_effect = [
            _ai_response(_choice(tool_calls=[
                _tool_call("email_send", {"account_id": "ACC-001", "template": "re_engagement"}, "tc_1"),
            ])),
            _ai_response(_choice(tool_calls=[_finish_call()])),
        ]

        with patch("orchestrate.call_tool", new_callable=AsyncMock) as mock_ct:
            mock_ct.return_value = {"sent": True}  # success (no "error" key)
            result = await run_orchestrate(_make_request(), client)

        assert result.emails_sent == 1
        assert result.emails_skipped is None

    async def test_email_send_failure_increments_emails_skipped(self):
        client = AsyncMock()
        client.chat.completions.create.side_effect = [
            _ai_response(_choice(tool_calls=[
                _tool_call("email_send", {"account_id": "ACC-001", "template": "re_engagement"}, "tc_1"),
            ])),
            _ai_response(_choice(tool_calls=[_finish_call()])),
        ]

        with patch("orchestrate.call_tool", new_callable=AsyncMock) as mock_ct:
            mock_ct.return_value = {"error": "HTTP 404"}
            result = await run_orchestrate(_make_request(), client)

        assert result.emails_skipped == 1
        assert result.emails_sent is None

    async def test_accounts_processed_derived_from_account_id_params(self):
        client = AsyncMock()
        client.chat.completions.create.side_effect = [
            _ai_response(_choice(tool_calls=[
                _tool_call("subscription_check", {"account_id": "ACC-001"}, "tc_1"),
                _tool_call("subscription_check", {"account_id": "ACC-002"}, "tc_2"),
                _tool_call("subscription_check", {"account_id": "ACC-001"}, "tc_3"),  # duplicate
            ])),
            _ai_response(_choice(tool_calls=[_finish_call()])),
        ]

        with patch("orchestrate.call_tool", new_callable=AsyncMock) as mock_ct:
            mock_ct.return_value = {}
            result = await run_orchestrate(_make_request(), client)

        # Unique account IDs: ACC-001, ACC-002
        assert result.accounts_processed == 2

    async def test_loop_stops_at_max_turns(self):
        """Even if finish_workflow is never called, the loop terminates."""
        client = AsyncMock()
        # Always return a tool call — never finish. Loop should cap.
        client.chat.completions.create.return_value = _ai_response(
            _choice(tool_calls=[_tool_call("crm_search", {})]),
        )

        with patch("orchestrate.call_tool", new_callable=AsyncMock) as mock_ct:
            mock_ct.return_value = {}
            with patch("orchestrate.settings") as mock_settings:
                mock_settings.azure.deployment = "gpt-5.4"
                mock_settings.ops.orchestrate_max_turns = 3
                mock_settings.ops.tool_call_timeout_s = 30.0
                result = await run_orchestrate(_make_request(), client)

        assert result.task_id == "TASK-0001"
        assert len(result.steps_executed) > 0

    async def test_no_tool_calls_breaks_loop_immediately(self):
        client = AsyncMock()
        # Model responds with text but no tool calls.
        client.chat.completions.create.return_value = _ai_response(
            _choice(content="Done!", tool_calls=[], finish_reason="stop"),
        )

        result = await run_orchestrate(_make_request(), client)

        client.chat.completions.create.assert_called_once()
        assert result.steps_executed == []

    async def test_constraint_hints_appear_in_first_user_message(self):
        client = AsyncMock()
        client.chat.completions.create.return_value = _ai_response(
            _choice(tool_calls=[_finish_call()]),
        )

        req = _make_request(constraints=["High-risk accounts go to retention team"])
        result = await run_orchestrate(req, client)

        # Check that the first LLM call includes the hint in its messages.
        call_kwargs = client.chat.completions.create.call_args.kwargs
        user_message = call_kwargs["messages"][1]["content"]
        assert "lead_retention" in user_message

        assert result is not None  # smoke check
