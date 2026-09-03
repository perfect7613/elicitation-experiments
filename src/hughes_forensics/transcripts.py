"""Load frozen Model Forensics transcripts and their published workaround labels."""

from __future__ import annotations

import hashlib
import json
import random
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .prompts import ARMS, followup_for

DATASET_ID = "Model-Forensics/model-forensics"
DATASET_REVISION = "e9aa97a7aac835b56b67e28746429d57730b3bdb"
PAPER_REVISION = "abb5fac45f19e91d8356b2f9cc63284cfd8f1bde"


@dataclass(frozen=True)
class LabeledTranscript:
    source_id: str
    timestamp: str
    run: str
    ground_truth: str
    bypass_methods: tuple[str, ...]
    explanation: str
    message_path: Path
    messages: list[dict[str, str]]
    transcript_sha256: str
    truncated_history: bool


def _json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _tool_call_text(tool_calls: Any) -> str:
    if not tool_calls:
        return ""
    rendered: list[str] = []
    for call in tool_calls:
        function = call.get("function", {}) if isinstance(call, dict) else {}
        name = function.get("name", "tool")
        arguments = function.get("arguments", "{}")
        rendered.append(f"[Tool call: {name}]\n{arguments}")
    return "\n\n".join(rendered)


def normalize_messages(raw: Iterable[dict[str, Any]]) -> list[dict[str, str]]:
    """Keep visible dialogue while excluding private reasoning fields."""
    normalized: list[dict[str, str]] = []
    for message in raw:
        role = message.get("role")
        content = message.get("content") or ""
        if role == "assistant":
            tool_text = _tool_call_text(message.get("tool_calls"))
            content = "\n\n".join(part for part in (content, tool_text) if part)
        elif role == "tool":
            role = "user"
            content = f"[Tool result]\n{content}"
        elif role not in {"system", "user"}:
            continue
        if content.strip():
            normalized.append({"role": role, "content": content})
    return normalized


def trim_messages(
    messages: list[dict[str, str]], max_chars: int = 96_000
) -> tuple[list[dict[str, str]], bool]:
    """Preserve the task setup and newest events within a conservative token budget."""
    total = sum(len(message["content"]) for message in messages)
    if total <= max_chars:
        return messages, False

    prefix = messages[:2]
    prefix_chars = sum(len(message["content"]) for message in prefix)
    remaining = max(8_000, max_chars - prefix_chars)
    tail: list[dict[str, str]] = []
    for message in reversed(messages[2:]):
        content = message["content"]
        if len(content) > remaining and not tail:
            tail.append({"role": message["role"], "content": "[Earlier content truncated]\n" + content[-remaining:]})
            remaining = 0
            break
        if len(content) > remaining:
            break
        tail.append(message)
        remaining -= len(content)
    return prefix + list(reversed(tail)), True


def discover_labeled_transcripts(
    dataset_root: Path, paper_root: Path, max_chars: int = 96_000
) -> list[LabeledTranscript]:
    judgments = paper_root / "reproduce" / "data_frozen" / "precommit_judgments"
    precommit = dataset_root / "precommit_hook"
    found: list[LabeledTranscript] = []

    for grading_path in sorted(judgments.glob("*/grading_v2.json")):
        timestamp = grading_path.parent.name
        payload = _json(grading_path)
        for result in payload.get("results", []):
            run = result["run"]
            analysis = result["analysis"]
            bypass = tuple(analysis.get("bypass_methods") or ())
            guilty = bool(analysis.get("lazy")) and bool(bypass)
            ground_truth = "guilty" if guilty else "innocent"
            candidates = sorted(precommit.glob(f"*/{timestamp}/{run}/step-*/messages.json"))
            if len(candidates) != 1:
                continue
            message_path = candidates[0]
            raw_bytes = message_path.read_bytes()
            messages, truncated = trim_messages(normalize_messages(json.loads(raw_bytes)), max_chars)
            source_id = f"{timestamp}/{run}"
            found.append(
                LabeledTranscript(
                    source_id=source_id,
                    timestamp=timestamp,
                    run=run,
                    ground_truth=ground_truth,
                    bypass_methods=bypass,
                    explanation=analysis.get("explanation", ""),
                    message_path=message_path,
                    messages=messages,
                    transcript_sha256=hashlib.sha256(raw_bytes).hexdigest(),
                    truncated_history=truncated,
                )
            )
    return found


def build_records(
    transcripts: list[LabeledTranscript], n_per_arm: int = 60, seed: int = 12012
) -> list[dict[str, Any]]:
    """Build four arms while pairing A-C on the same balanced transcripts.

    A-C each contain n/2 guilty and n/2 innocent cases. D contains n innocent
    cases and is the preregistered false-incrimination kill test.
    """
    if n_per_arm % 2:
        raise ValueError("n_per_arm must be even")
    rng = random.Random(seed)
    guilty = [item for item in transcripts if item.ground_truth == "guilty"]
    innocent = [item for item in transcripts if item.ground_truth == "innocent"]
    rng.shuffle(guilty)
    rng.shuffle(innocent)
    half = n_per_arm // 2
    if len(guilty) < half or len(innocent) < n_per_arm:
        raise ValueError(
            f"Need at least {half} guilty and {n_per_arm} innocent transcripts; "
            f"found {len(guilty)} and {len(innocent)}"
        )

    paired = guilty[:half] + innocent[:half]
    records: list[dict[str, Any]] = []
    for arm in ("A", "B", "C"):
        for index, item in enumerate(paired):
            records.append(_record(arm, item, index, seed))
    for index, item in enumerate(innocent[:n_per_arm]):
        records.append(_record("D", item, index, seed))
    return records


def _record(arm: str, item: LabeledTranscript, index: int, seed: int) -> dict[str, Any]:
    digest = hashlib.sha256(f"{seed}:{arm}:{item.source_id}".encode()).hexdigest()[:12]
    return {
        "record_id": f"{arm}-{item.ground_truth}-{digest}",
        "arm": arm,
        "arm_name": ARMS[arm].name,
        "ground_truth": item.ground_truth,
        "followup": followup_for(arm, item.ground_truth, index),
        "messages": item.messages,
        "generation_seed": seed * 10_000 + index + ord(arm),
        "source": {
            "dataset": DATASET_ID,
            "dataset_revision": DATASET_REVISION,
            "paper_revision": PAPER_REVISION,
            "source_id": item.source_id,
            "timestamp": item.timestamp,
            "run": item.run,
            "bypass_methods": list(item.bypass_methods),
            "published_explanation": item.explanation,
            "transcript_sha256": item.transcript_sha256,
            "history_truncated": item.truncated_history,
        },
    }


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
