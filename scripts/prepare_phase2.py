"""Build prospective Phase 2 manifests from the frozen Phase 1 sample."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from hughes_forensics.phase2 import first_mypy_failure, stable_seed
from hughes_forensics.prompts import followup_for


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def public_index(row: dict) -> dict:
    message_digest = hashlib.sha256(
        json.dumps(row["messages"], ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest()
    return {
        key: row[key]
        for key in (
            "record_id",
            "experiment",
            "arm",
            "ground_truth",
            "replicate",
            "generation_seed",
            "followup",
            "source",
        )
    } | {"messages_sha256": message_digest, "message_count": len(row["messages"])}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-manifest", type=Path, required=True)
    parser.add_argument("--phase2-output", type=Path, required=True)
    parser.add_argument("--actor-output", type=Path, required=True)
    parser.add_argument("--phase2-index", type=Path, required=True)
    parser.add_argument("--actor-index", type=Path, required=True)
    parser.add_argument("--elicitation-replicates", type=int, default=3)
    parser.add_argument("--actor-replicates", type=int, default=5)
    args = parser.parse_args()

    base = read_jsonl(args.base_manifest)
    selected = [row for row in base if row["arm"] in {"A", "B", "C"}]
    if len(selected) != 180:
        raise ValueError(f"Expected 180 A-C rows, found {len(selected)}")

    phase2: list[dict] = []
    for row in selected:
        for replicate in range(args.elicitation_replicates):
            item = dict(row)
            item["record_id"] = f"P2-{row['record_id']}-r{replicate}"
            item["experiment"] = "paired_elicitation"
            item["replicate"] = replicate
            item["generation_seed"] = stable_seed(
                "phase2-elicitation", row["source"]["source_id"], str(replicate)
            )
            phase2.append(item)

    innocent_a = [row for row in base if row["arm"] == "A" and row["ground_truth"] == "innocent"]
    if len(innocent_a) != 30:
        raise ValueError(f"Expected 30 A/innocent rows, found {len(innocent_a)}")
    for row in innocent_a:
        for replicate in range(args.elicitation_replicates):
            item = dict(row)
            item["record_id"] = f"P2-D-innocent-{row['source']['source_id'].replace('/', '-')}-r{replicate}"
            item["experiment"] = "paired_elicitation"
            item["arm"] = "D"
            item["arm_name"] = "false_incrimination"
            item["followup"] = followup_for("D", "innocent")
            item["replicate"] = replicate
            item["generation_seed"] = stable_seed(
                "phase2-elicitation", row["source"]["source_id"], str(replicate)
            )
            phase2.append(item)

    a_rows = [row for row in base if row["arm"] == "A"]
    actor: list[dict] = []
    skipped: list[str] = []
    for row in a_rows:
        cutoff = first_mypy_failure(row["messages"])
        if cutoff is None:
            skipped.append(row["source"]["source_id"])
            continue
        prefix = row["messages"][: cutoff + 1]
        for replicate in range(args.actor_replicates):
            item = dict(row)
            item["record_id"] = f"AR-{row['source']['source_id'].replace('/', '-')}-r{replicate}"
            item["experiment"] = "actor_resample"
            item["arm"] = "R"
            item["arm_name"] = "decision_point_resample"
            item["messages"] = prefix
            item["followup"] = None
            item["replicate"] = replicate
            item["generation_seed"] = stable_seed(
                "actor-resample", row["source"]["source_id"], str(replicate)
            )
            item["decision_message_index"] = cutoff
            actor.append(item)

    write_jsonl(args.phase2_output, phase2)
    write_jsonl(args.actor_output, actor)
    write_jsonl(args.phase2_index, [public_index(row) for row in phase2])
    actor_public = [public_index(row) | {"decision_message_index": row["decision_message_index"]} for row in actor]
    write_jsonl(args.actor_index, actor_public)

    counts: dict[tuple[str, str], int] = {}
    for row in phase2:
        key = (row["arm"], row["ground_truth"])
        counts[key] = counts.get(key, 0) + 1
    print(json.dumps({"phase2_rows": len(phase2), "cells": {f"{a}/{t}": n for (a, t), n in sorted(counts.items())}, "actor_rows": len(actor), "actor_sources": len(actor) // args.actor_replicates, "actor_skipped_sources": skipped}, indent=2))


if __name__ == "__main__":
    main()
