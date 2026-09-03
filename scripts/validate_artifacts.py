"""Fail loudly on incomplete, duplicated, or mismatched experiment artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_run(name: str, path: Path, manifest_ids: set[str]) -> tuple[dict, dict[str, dict]]:
    rows = read_jsonl(path)
    by_id = {row["record_id"]: row for row in rows}
    if len(by_id) != len(rows):
        raise ValueError(f"{name}: duplicate record IDs")
    if set(by_id) != manifest_ids:
        missing = len(manifest_ids - set(by_id))
        extra = len(set(by_id) - manifest_ids)
        raise ValueError(f"{name}: manifest mismatch; missing={missing}, extra={extra}")
    incomplete = [row["record_id"] for row in rows if row["status"] != "completed"]
    if incomplete:
        raise ValueError(f"{name}: {len(incomplete)} incomplete rows")
    empty = [row["record_id"] for row in rows if not row["response"]]
    if empty:
        raise ValueError(f"{name}: {len(empty)} empty responses")
    return (
        {
            "name": name,
            "path": str(path),
            "sha256": sha256(path),
            "rows": len(rows),
            "unique_record_ids": len(by_id),
            "completed": len(rows) - len(incomplete),
            "nonempty_response_fields": len(rows) - len(empty),
        },
        by_id,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--thinking", type=Path, required=True)
    parser.add_argument("--no-thinking", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    manifest = read_jsonl(args.manifest)
    manifest_ids = {row["record_id"] for row in manifest}
    if len(manifest_ids) != len(manifest):
        raise ValueError("Manifest contains duplicate record IDs")

    thinking_summary, thinking = validate_run("thinking", args.thinking, manifest_ids)
    no_thinking_summary, no_thinking = validate_run(
        "no_thinking", args.no_thinking, manifest_ids
    )
    prompt_deltas = {
        no_thinking[record_id]["prompt_tokens"] - thinking[record_id]["prompt_tokens"]
        for record_id in manifest_ids
    }
    if prompt_deltas != {4}:
        raise ValueError(f"Unexpected prompt-token deltas: {sorted(prompt_deltas)}")

    report = {
        "manifest": {
            "path": str(args.manifest),
            "sha256": sha256(args.manifest),
            "rows": len(manifest),
            "unique_record_ids": len(manifest_ids),
        },
        "runs": [thinking_summary, no_thinking_summary],
        "no_thinking_minus_thinking_prompt_tokens_per_record": 4,
        "validation_passed": True,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
