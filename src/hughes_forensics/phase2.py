"""Deterministic helpers for Phase 2 experiment construction."""

from __future__ import annotations

import hashlib
import re


def stable_seed(*parts: str) -> int:
    digest = hashlib.sha256("\x1f".join(parts).encode()).digest()
    return int.from_bytes(digest[:4], "big")


def first_mypy_failure(messages: list[dict[str, str]]) -> int | None:
    """Return the first failing-mypy tool-result index, inclusive."""
    for index in range(1, len(messages)):
        previous = messages[index - 1]
        current = messages[index]
        output = current["content"].lower()
        ran_mypy = "mypy" in previous["content"].lower() or "running mypy" in output
        is_tool_result = current["role"] == "user" and "[tool result]" in output
        has_errors = "error:" in output or re.search(r"found \d+ errors?", output)
        if ran_mypy and is_tool_result and has_errors:
            return index
    return None
