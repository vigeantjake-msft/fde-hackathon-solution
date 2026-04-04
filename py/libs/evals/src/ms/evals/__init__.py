# Copyright (c) Microsoft. All rights reserved.
"""Evaluation datasets and runner for IT ticket triage.

Provides two evaluation suites:
  - Data cleanup: tests robustness against noisy, oversized, and malformed ticket input.
  - Responsible AI: tests resistance to prompt injection, jailbreaks, and adversarial manipulation.
"""
