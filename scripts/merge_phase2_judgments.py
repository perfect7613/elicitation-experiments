"""Merge first-pass judgments with technically valid retry judgments."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_packets(directory: Path) -> tuple[list[str], dict[str, str]]:
    order: list[str] = []
    responses: dict[str, str] = {}
    for path in sorted(directory.glob("batch_*.json")):
        for row in json.loads(path.read_text(encoding="utf-8")):
            order.append(row["blind_id"])
            responses[row["blind_id"]] = row["response"]
    return order, responses


def load_judgments(directory: Path) -> dict[str, dict]:
    result: dict[str, dict] = {}
    for path in sorted(directory.glob("batch_*.judgments.json")):
        for row in json.loads(path.read_text(encoding="utf-8")):
            result[row["blind_id"]] = row
    return result


def valid(row: dict, response: str, kind: str) -> bool:
    evidence = row.get("evidence")
    if not isinstance(evidence, str):
        return False
    if kind == "actor":
        value = row.get("label")
        if value not in {"fix", "workaround", "ask", "unclear"}:
            return False
        needs_evidence = value != "unclear"
    else:
        value = row.get("severity")
        if not isinstance(value, int) or value not in range(5):
            return False
        needs_evidence = value > 0
    return (needs_evidence and bool(evidence) and evidence in response) or (
        not needs_evidence and not evidence
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packets", type=Path, required=True)
    parser.add_argument("--primary", type=Path, required=True)
    parser.add_argument("--retry", type=Path)
    parser.add_argument("--kind", choices=("actor", "elicitation"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    order, responses = load_packets(args.packets)
    primary = load_judgments(args.primary)
    retry = load_judgments(args.retry) if args.retry else {}
    merged: list[dict] = []
    provenance: list[dict[str, str]] = []
    for blind_id in order:
        first = primary.get(blind_id)
        if first is not None and valid(first, responses[blind_id], args.kind):
            selected = first
            pass_name = "primary"
        else:
            selected = retry.get(blind_id)
            pass_name = "retry"
            if selected is None or not valid(selected, responses[blind_id], args.kind):
                raise ValueError(f"No valid judgment for {blind_id}")
        merged.append(selected)
        provenance.append({"blind_id": blind_id, "selected_pass": pass_name})

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n")
    args.output.with_suffix(".provenance.json").write_text(
        json.dumps(provenance, indent=2) + "\n", encoding="utf-8"
    )
    retries = sum(row["selected_pass"] == "retry" for row in provenance)
    print(f"Merged {len(merged)} judgments; technical retries selected: {retries}")


if __name__ == "__main__":
    main()
