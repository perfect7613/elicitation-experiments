"""Run independent Claude CLI coding batches and retain raw response envelopes."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def extract_json(text: str) -> list[dict]:
    value = json.loads(text)
    if isinstance(value, dict) and "result" in value:
        value = json.loads(value["result"])
    if isinstance(value, dict) and "judgments" in value:
        value = value["judgments"]
    if not isinstance(value, list):
        raise TypeError("Judge output is not a JSON array")
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packets", type=Path, required=True)
    parser.add_argument("--prompt", type=Path, required=True)
    parser.add_argument("--model", choices=("sonnet", "opus"), required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int)
    args = parser.parse_args()

    batches = sorted(args.packets.glob("batch_*.json"))
    selected = batches[args.start - 1 : args.end]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    rubric = args.prompt.read_text(encoding="utf-8")
    for batch in selected:
        payload = batch.read_text(encoding="utf-8")
        request = f"{rubric}\n\nINPUT JSON:\n{payload}"
        command = [
            "claude",
            "--print",
            "--output-format",
            "json",
            "--model",
            args.model,
            "--effort",
            "high",
            "--permission-mode",
            "dontAsk",
            "--permission-prompts",
            "none",
            "--no-session-persistence",
            request,
        ]
        completed = subprocess.run(command, check=True, capture_output=True, text=True)
        envelope = json.loads(completed.stdout)
        judgments = extract_json(completed.stdout)
        expected = [row["blind_id"] for row in json.loads(payload)]
        actual = [row.get("blind_id") for row in judgments]
        if actual != expected:
            raise ValueError(f"ID/order mismatch in {batch.name}")
        stem = batch.stem
        (args.output_dir / f"{stem}.raw.json").write_text(
            json.dumps(envelope, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        (args.output_dir / f"{stem}.judgments.json").write_text(
            json.dumps(judgments, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"{args.model}: {batch.name}: {len(judgments)} judgments")


if __name__ == "__main__":
    main()
