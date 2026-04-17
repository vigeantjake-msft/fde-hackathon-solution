"""Prompt loader — reads system prompts from YAML files at import time.

Externalising prompts from code allows them to be:
  - Reviewed and edited without touching Python source
  - Version-controlled and diffed as plain text
  - Swapped per-environment via environment-variable overrides
  - Tested independently from business logic

Usage::

    from prompts import load_prompt
    system_prompt = load_prompt("triage")
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

_PROMPT_DIR = Path(__file__).parent


def load_prompt(name: str) -> str:
    """Load the system prompt for *name* from ``prompts/{name}.yaml``.

    The YAML file must contain a top-level ``system`` key whose value is the
    full system prompt string.

    An environment variable ``PROMPT_{NAME_UPPER}`` can override the file
    path, enabling per-environment prompt injection without a rebuild.

    Args:
        name: Prompt name, e.g. ``"triage"``, ``"extract"``, ``"orchestrate"``.

    Returns:
        The system prompt string.

    Raises:
        FileNotFoundError: If the YAML file does not exist.
        KeyError: If the YAML file does not contain a ``system`` key.
    """
    env_override = os.environ.get(f"PROMPT_{name.upper()}_PATH")
    path = Path(env_override) if env_override else _PROMPT_DIR / f"{name}.yaml"

    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")

    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if "system" not in data:
        raise KeyError(f"Prompt file {path} missing required 'system' key")

    logger.debug("loaded_prompt name=%s path=%s chars=%d", name, path, len(data["system"]))
    return data["system"]
