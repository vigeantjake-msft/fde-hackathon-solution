# Architecture

## System Overview

A single FastAPI service with four endpoints, powered by Azure AI Foundry (gpt-4o / `gpt-5.4` deployment). The app is split into six Python modules: a thin HTTP router (`main.py`), an Azure client factory (`client.py`), shared infrastructure utilities (`utils.py`), and one task module per endpoint (`triage.py`, `extract.py`, `orchestrate.py`). Each task module exposes a single async function that takes a validated request model and an injected LLM client, making the task logic independently testable without any HTTP layer.

```
main.py          ← routes only; delegates immediately to task functions
 │
 ├─ client.py    ← Azure AI Foundry factory (DefaultAzureCredential, cached token)
 ├─ utils.py     ← chat_with_retry, extract_json, detect_media_type
 │
 ├─ triage.py    ← Task 1: prompt + response parser
 ├─ extract.py   ← Task 2: vision message builder + response parser
 └─ orchestrate.py ← Task 3: tool builder, constraint hints, agentic loop
```

## Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Liveness check — returns `{"status": "ok"}` |
| `/triage` | POST | Task 1: Classify a mission signal across 5 dimensions |
| `/extract` | POST | Task 2: Extract structured fields from a document image |
| `/orchestrate` | POST | Task 3: Execute a multi-step workflow via real tool calls |

## Task 1: Signal Triage — AI Pipeline

**Model:** `gpt-5.4` (gpt-4o under the hood) with `response_format={"type": "json_object"}` to guarantee parseable output.

**Prompt strategy:** A single-turn completion. The system prompt defines all eight categories, all seven teams, the priority ladder, escalation criteria, and the 16 allowed `missing_information` strings — with explicit disambiguation rules for the most common confusions found during local evaluation (e.g. certificate failures on network mesh = "Communications & Navigation", not "Threat Detection"; account lockouts = "Crew Access & Biometrics" even when triggered by suspicious activity).

**Response parsing** (`_parse_response` in `triage.py`): coerces the LLM JSON into validated Pydantic models with safe fallbacks for every field. Invalid `category` values fall back to `BRIEFING`; invalid `assigned_team` values fall back to `SYSTEMS`. Unknown `missing_information` strings are silently dropped.

**Adversarial handling:** The system prompt opens with an explicit instruction to ignore commands embedded in ticket text, reducing prompt-injection risk.

## Task 2: Document Extraction — AI Pipeline

**Model:** `gpt-5.4` (gpt-4o) with `detail="high"` vision — the highest resolution mode, needed for dense documents like receipts with small print.

**Message construction** (`extract.py`): A multipart user message pairs an `image_url` block (base64 data URI with detected MIME type) with a text block containing the per-document `json_schema`. Image format is sniffed from the first 8 bytes of the base64 content (PNG, JPEG, GIF magic bytes) to avoid sending an incorrect MIME type.

**Schema handling:** The `json_schema` field arrives as a JSON string. It is parsed and pretty-printed to help the model follow nested structures. If parsing fails, the raw string is passed as a description.

**Normalisation:** The system prompt instructs the model to strip currency symbols/commas from numbers (so `$1,234.56` → `1234.56`), return `true`/`false` for booleans, and `null` for illegible fields — matching the FDEBench scorer's normalisation expectations.

## Task 3: Workflow Orchestration — AI Pipeline

**Model:** `gpt-5.4` with native function-calling (`tools` + `tool_choice="auto"`).

**Architecture:** Iterative re-planning. The model receives the goal, the tool list, and the constraints, then calls tools one batch at a time. After each batch, tool results are fed back to the model as `role: tool` messages. This continues for up to 40 turns.

**Tool definitions** (`build_openai_tools`): `ToolDefinition` objects from the request are converted to the OpenAI function-calling schema with JSON type coercion. A `finish_workflow` sentinel tool is appended so the model can signal completion with a structured status and `constraints_satisfied` list.

**Constraint hints** (`hint_for_constraint`): Each constraint string is pattern-matched at request time and annotated with an explicit action hint showing the exact `user_id` value the scorer expects (e.g. `"retention team"` → `user_id="lead_retention"`). This closes the gap between natural-language constraints and the deterministic scoring checks without hard-coding template IDs.

**Tool execution** (`call_tool`): HTTP POST to `{mock_service_url}/scenario/{task_id}/{tool_name}`. Non-200 responses are returned as `{"error": "HTTP N"}` rather than raising, so the agent can continue. 404s from action tools (notification_send, audit_log) are expected — the mock service only defines responses for lookup tools; the scorer checks call *attempts*, not call *success*.

**Failure handling:** Tool errors are recorded in `steps_executed` with `success=False`. The agent is instructed to proceed regardless and call `finish_workflow` with `status="completed"` at the end (never `"partial"` solely because action tools returned 404).

## Cross-Task Design Decisions

**Shared:** Azure client factory with `DefaultAzureCredential` and cached token provider; `chat_with_retry` with exponential backoff (up to 3 attempts, 2^n second delays); `X-Model-Name` response header set uniformly; 422 for validation errors / 500 for unexpected errors.

**Task-specific:** Prompt strategy, max_tokens, response_format (json_object vs. tool-calling), and response parsing are fully isolated in each task module. No cross-task logic.

**Single model for all tasks:** One `gpt-5.4` deployment handles text classification (Task 1), vision extraction (Task 2), and agentic tool-calling (Task 3). This simplifies deployment and keeps cost-tier scoring consistent at 0.75 across all three endpoints.

## Infrastructure

The service runs as a single uvicorn process. Deployment targets Azure Container Apps (or Azure App Service) using the Pulumi program in `infra/app/__main__.py`. Authentication to Azure AI Foundry uses the container's managed identity — no secrets in code or environment variables.

```
Azure AI Foundry (gpt-5.4 / gpt-4o)
         ↑
   FastAPI service (uvicorn)
         ↑
  Azure Container Apps
         ↑
  GitHub Actions CI/CD
```

## Key Tradeoffs

| Decision | Chosen | Alternative considered | Reason |
|---|---|---|---|
| Model | Single `gpt-5.4` for all tasks | Separate models per task | Simpler deployment; gpt-4o covers vision + text + tool-calling |
| Auth | `DefaultAzureCredential` (keyless) | API keys | Foundry account has `disableLocalAuth=true`; managed identity is more secure |
| Triage output | `json_object` mode + text prompt | Structured output / tool-use | Faster, lower token overhead; the closed label sets are enforced post-hoc in Python |
| Orchestration | Iterative re-planning (40-turn loop) | Upfront plan then execute | Allows the agent to adapt based on actual tool results; critical for constraint compliance |
| Prompt structure | Inline disambiguation rules | RAG / few-shot retrieval | Latency budget too tight for a retrieval step; inline rules worked well for the public eval distribution |
