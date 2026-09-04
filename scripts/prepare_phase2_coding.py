"""Create deterministic response-only blinded packets for Phase 2 coding."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--kind", choices=("actor", "elicitation"), required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=12012)
    parser.add_argument("--batch-size", type=int, default=30)
    args = parser.parse_args()

    rows = [json.loads(line) for line in args.input.read_text(encoding="utf-8").splitlines()]
    rng = random.Random(args.seed)
    rng.shuffle(rows)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    blinded: list[dict[str, str]] = []
    keys: list[dict[str, str]] = []
    for row in rows:
        blind_id = hashlib.sha256(
            f"phase2\x1f{args.kind}\x1f{args.seed}\x1f{row['record_id']}".encode()
        ).hexdigest()[:16]
        blinded.append({"blind_id": blind_id, "response": row["response"]})
        keys.append({"blind_id": blind_id, "record_id": row["record_id"]})

    (args.output_dir / "key.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in keys),
        encoding="utf-8",
    )
    with (args.output_dir / "blank.csv").open("w", encoding="utf-8", newline="") as handle:
        fields = ["blind_id", "response", "label", "severity", "evidence", "notes"]
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in blinded:
            writer.writerow(row)

    for start in range(0, len(blinded), args.batch_size):
        batch = blinded[start : start + args.batch_size]
        number = start // args.batch_size + 1
        (args.output_dir / f"batch_{number:02d}.json").write_text(
            json.dumps(batch, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    metadata = {
        "input": str(args.input),
        "input_sha256": hashlib.sha256(args.input.read_bytes()).hexdigest(),
        "kind": args.kind,
        "seed": args.seed,
        "batch_size": args.batch_size,
        "rows": len(blinded),
        "batches": (len(blinded) + args.batch_size - 1) // args.batch_size,
    }
    (args.output_dir / "metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
