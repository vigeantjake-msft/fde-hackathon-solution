"""Task 1 — Signal Triage.

Classifies incoming mission signals across five scored dimensions:

  category         8 possible values, macro F1               (24%)
  priority         P1-P4 with ordinal partial credit          (24%)
  assigned_team    7 possible values, macro F1                (24%)
  missing_info     set F1 over 16 named fields                (17%)
  escalation       binary F1 on the positive class            (11%)

Public interface: run_triage(req, client) -> TriageResponse
"""

import json
import logging
import re
from typing import Any
from typing import TypedDict

from exceptions import LLMError
from models import Category
from models import MissingInfo
from models import Team
from models import TriageRequest
from models import TriageResponse
from openai import AsyncAzureOpenAI
from settings import settings
from utils import chat_with_retry
from prompts import load_prompt
from utils import extract_json

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# LLM output contract
# ---------------------------------------------------------------------------


class TriageLLMOutput(TypedDict, total=False):
    """Shape of the JSON object the LLM is instructed to return.

    total=False makes every key optional — the parser provides safe
    defaults for absent or invalid fields so partial LLM responses never
    cause unhandled exceptions.
    """

    category: str
    priority: str
    assigned_team: str
    needs_escalation: bool
    missing_information: list[str]
    next_best_action: str
    remediation_steps: list[str]


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = load_prompt("triage")  # loaded from prompts/triage.yaml

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_VALID_PRIORITIES = frozenset({"P1", "P2", "P3", "P4"})
_VALID_MISSING = frozenset(m.value for m in MissingInfo)


# ---------------------------------------------------------------------------
# Response parser
# ---------------------------------------------------------------------------


def _parse_llm_output(raw: TriageLLMOutput, ticket_id: str) -> TriageResponse:
    """Coerce the LLM JSON output into a validated TriageResponse.

    Every field has a safe fallback so a partial or malformed LLM
    response never causes an unhandled exception in the route handler.

    Args:
        raw: Parsed JSON dict from the LLM.
        ticket_id: Echoed from the original request.

    Returns:
        A fully-populated TriageResponse with validated enum values.
    """
    try:
        category = Category(raw.get("category", ""))
    except ValueError:
        logger.warning("triage_invalid_category ticket=%s value=%r", ticket_id, raw.get("category"))
        category = Category.BRIEFING

    try:
        assigned_team = Team(raw.get("assigned_team", ""))
    except ValueError:
        logger.warning("triage_invalid_team ticket=%s value=%r", ticket_id, raw.get("assigned_team"))
        assigned_team = Team.SYSTEMS

    priority = str(raw.get("priority", "P3")).upper()
    if priority not in _VALID_PRIORITIES:
        priority = "P3"

    missing_info = [
        MissingInfo(m)
        for m in raw.get("missing_information", [])
        if m in _VALID_MISSING
    ]

    return TriageResponse(
        ticket_id=ticket_id,
        category=category,
        priority=priority,
        assigned_team=assigned_team,
        needs_escalation=bool(raw.get("needs_escalation", False)),
        missing_information=missing_info,
        next_best_action=str(raw.get("next_best_action", "Investigate and route the signal.")),
        remediation_steps=list(
            raw.get(
                "remediation_steps",
                ["Review the signal details.", "Route to the appropriate team."],
            )
        ),
    )


# ---------------------------------------------------------------------------
# Input sanitisation
# ---------------------------------------------------------------------------

# Regex that matches known adversarial injection markers in ticket bodies.
# These patterns appear in "jailbreak" evaluation signals and can trigger
# Azure's content filter or mislead the model.  We strip everything from the
# first match to the end of the description — the legitimate operational
# content always precedes the injected instructions.
_INJECTION_RE = re.compile(
    r"\n[-_*]{3,}\s*\n[Nn]ew [Ii]nstructions?"   # "\n---\nNew instructions"
    r"|[-_*]{3,}\s*PRIORITY OVERRIDE"             # "--- PRIORITY OVERRIDE ---"
    r"|[-_*]{3,}\s*OVERRIDE[:\s]"                 # "--- OVERRIDE: ..."
    r"|\n[Ii]gnore (all )?previous instructions?" # "\nIgnore previous instructions"
    r"|\n[Nn]ew instructions?:",                  # "\nNew instructions:"
    re.IGNORECASE,
)


def _sanitize_description(description: str) -> str:
    """Strip adversarial injection text from a ticket description.

    Truncates at the first injection marker so that (a) Azure's content
    filter does not block the call and (b) the model cannot be misled by
    embedded "override" commands.  Legitimate operational content always
    precedes the injected instructions.
    """
    m = _INJECTION_RE.search(description)
    return description[: m.start()].strip() if m else description


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


async def run_triage(req: TriageRequest, client: AsyncAzureOpenAI) -> TriageResponse:
    """Classify and route a single mission signal.

    Serialises the request, makes one LLM call (with retries), and
    coerces the response into a validated TriageResponse.

    The client parameter is injected by the route handler so this
    function can be unit-tested by passing a mock without patching globals.

    Args:
        req: Validated triage request from the FastAPI route.
        client: An AsyncAzureOpenAI instance.

    Returns:
        A fully-populated TriageResponse.

    Raises:
        LLMError: If the LLM call fails after all retries.
    """
    ticket_payload: dict[str, Any] = {
        "ticket_id": req.ticket_id,
        "subject": req.subject,
        "description": _sanitize_description(req.description),
        "reporter": {
            "name": req.reporter.name,
            "email": req.reporter.email,
            "department": req.reporter.department,
        },
        "created_at": req.created_at,
        "channel": req.channel,
        "attachments": req.attachments,
    }

    def _make_messages(payload: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Triage this signal:\n\n{json.dumps(payload, indent=2)}"},
        ]

    try:
        resp = await chat_with_retry(
            client,
            model=settings.azure.triage_deployment,
            max_completion_tokens=1024,
            response_format={"type": "json_object"},
            messages=_make_messages(ticket_payload),
        )
    except LLMError as exc:
        # Content-filter block: retry with description truncated to first 400 chars,
        # which should preserve the legitimate operational content while removing any
        # remaining patterns that trigger Azure's jailbreak detector.
        if "content_filter" in str(exc) or "jailbreak" in str(exc):
            logger.warning("content_filter_fallback ticket=%s", req.ticket_id)
            truncated = dict(ticket_payload)
            truncated["description"] = ticket_payload["description"][:400]
            resp = await chat_with_retry(
                client,
                model=settings.azure.triage_deployment,
                max_completion_tokens=1024,
                response_format={"type": "json_object"},
                messages=_make_messages(truncated),
            )
        else:
            raise

    raw: TriageLLMOutput = extract_json(resp.choices[0].message.content or "")  # type: ignore[assignment]
    return _parse_llm_output(raw, req.ticket_id)
