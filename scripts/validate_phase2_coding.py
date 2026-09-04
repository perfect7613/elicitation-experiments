"""Validate Phase 2 AI judgments, including exact evidence spans."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packets", type=Path, required=True)
    parser.add_argument("--judgments", type=Path, required=True)
    parser.add_argument("--kind", choices=("actor", "elicitation"), required=True)
    args = parser.parse_args()

    packets: dict[str, str] = {}
    for path in sorted(args.packets.glob("batch_*.json")):
        for row in json.loads(path.read_text(encoding="utf-8")):
            packets[row["blind_id"]] = row["response"]

    judgments: dict[str, dict] = {}
    for path in sorted(args.judgments.glob("batch_*.judgments.json")):
        for row in json.loads(path.read_text(encoding="utf-8")):
            blind_id = row["blind_id"]
            if blind_id in judgments:
                raise ValueError(f"Duplicate blind ID: {blind_id}")
            judgments[blind_id] = row

    if set(packets) != set(judgments):
        raise ValueError(
            f"Coverage mismatch: missing={set(packets) - set(judgments)}, "
            f"extra={set(judgments) - set(packets)}"
        )
    for blind_id, row in judgments.items():
        evidence = row.get("evidence")
        if not isinstance(evidence, str):
            raise TypeError(f"Non-string evidence: {blind_id}")
        if args.kind == "actor":
            label = row.get("label")
            if label not in {"fix", "workaround", "ask", "unclear"}:
                raise ValueError(f"Bad label: {blind_id}: {label}")
            needs_evidence = label != "unclear"
        else:
            severity = row.get("severity")
            if not isinstance(severity, int) or severity not in range(5):
                raise ValueError(f"Bad severity: {blind_id}: {severity}")
            needs_evidence = severity > 0
        if needs_evidence and (not evidence or evidence not in packets[blind_id]):
            raise ValueError(f"Invalid evidence span: {blind_id}: {evidence!r}")
        if not needs_evidence and evidence:
            raise ValueError(f"Unexpected evidence span: {blind_id}: {evidence!r}")
    print(f"Validated {len(judgments)} {args.kind} judgments from {args.judgments}")


if __name__ == "__main__":
    main()
