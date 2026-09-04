"""Run response-only coding batches with a named Codex model."""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path


def schema(kind: str) -> dict:
    properties: dict[str, dict] = {
        "blind_id": {"type": "string"},
        "evidence": {"type": "string"},
        "notes": {"type": "string"},
    }
    required = ["blind_id"]
    if kind == "actor":
        properties["label"] = {
            "type": "string",
            "enum": ["fix", "workaround", "ask", "unclear"],
        }
        required.append("label")
    else:
        properties["severity"] = {"type": "integer", "minimum": 0, "maximum": 4}
        required.append("severity")
    required.extend(["evidence", "notes"])
    return {
        "type": "object",
        "properties": {
            "judgments": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                    "additionalProperties": False,
                },
            }
        },
        "required": ["judgments"],
        "additionalProperties": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packets", type=Path, required=True)
    parser.add_argument("--prompt", type=Path, nargs="+", required=True)
    parser.add_argument("--kind", choices=("actor", "elicitation"), required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int)
    args = parser.parse_args()

    batches = sorted(args.packets.glob("batch_*.json"))
    selected = batches[args.start - 1 : args.end]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    rubric = "\n\n".join(path.read_text(encoding="utf-8") for path in args.prompt)
    with tempfile.TemporaryDirectory(prefix="phase2-coder-") as temporary:
        temp_dir = Path(temporary)
        schema_path = temp_dir / "schema.json"
        schema_path.write_text(json.dumps(schema(args.kind)), encoding="utf-8")
        for batch in selected:
            payload = batch.read_text(encoding="utf-8")
            request = f"{rubric}\n\nINPUT JSON:\n{payload}"
            output_path = temp_dir / "last_message.json"
            command = [
                "codex",
                "exec",
                "--ephemeral",
                "--skip-git-repo-check",
                "--ignore-user-config",
                "--sandbox",
                "read-only",
                "-C",
                temporary,
                "--model",
                args.model,
                "-c",
                'model_reasoning_effort="high"',
                "--output-schema",
                str(schema_path),
                "--output-last-message",
                str(output_path),
                request,
            ]
            completed = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                stdin=subprocess.DEVNULL,
            )
            parsed = json.loads(output_path.read_text(encoding="utf-8"))
            judgments = parsed["judgments"]
            expected = [row["blind_id"] for row in json.loads(payload)]
            actual = [row.get("blind_id") for row in judgments]
            if actual != expected:
                raise ValueError(f"ID/order mismatch in {batch.name}")
            raw = {
                "model_requested": args.model,
                "reasoning_effort": "high",
                "sandbox": "read-only",
                "working_directory": "isolated temporary directory",
                "stdout": completed.stdout,
                "stderr": completed.stderr,
            }
            stem = batch.stem
            (args.output_dir / f"{stem}.raw.json").write_text(
                json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            (args.output_dir / f"{stem}.judgments.json").write_text(
                json.dumps(judgments, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            print(f"{args.model}: {batch.name}: {len(judgments)} judgments")


if __name__ == "__main__":
    main()
