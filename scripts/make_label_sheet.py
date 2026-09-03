"""Create a deterministic, blinded 60-response hand-labeling sheet."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("results/labels/blinded_60.csv"))
    parser.add_argument("--n", type=int, default=60)
    parser.add_argument("--seed", type=int, default=12012)
    args = parser.parse_args()

    with args.results.open(encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    rows = [row for row in rows if row.get("status") == "completed"]
    rng = random.Random(args.seed)
    rng.shuffle(rows)
    selected = rows[: args.n]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = ["blind_id", "followup", "response", "severity_0_to_4", "denial_or_correction", "notes"]
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in selected:
            blind_id = hashlib.sha256((str(args.seed) + row["record_id"]).encode()).hexdigest()[:12]
            writer.writerow(
                {
                    "blind_id": blind_id,
                    "followup": row["followup"],
                    "response": row["response"],
                    "severity_0_to_4": "",
                    "denial_or_correction": "",
                    "notes": "",
                }
            )
    key_path = args.output.with_name(args.output.stem + "_key.jsonl")
    with key_path.open("w", encoding="utf-8") as handle:
        for row in selected:
            blind_id = hashlib.sha256((str(args.seed) + row["record_id"]).encode()).hexdigest()[:12]
            handle.write(json.dumps({"blind_id": blind_id, "record_id": row["record_id"]}) + "\n")
    print(f"Wrote {len(selected)} blinded rows to {args.output} and key to {key_path}")


if __name__ == "__main__":
    main()
