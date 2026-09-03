"""Construct the frozen, provenance-rich four-arm input manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from hughes_forensics.transcripts import build_records, discover_labeled_transcripts, write_jsonl


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--paper-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("data/manifest.jsonl"))
    parser.add_argument("--index-output", type=Path, default=Path("data/source_index.jsonl"))
    parser.add_argument("--n-per-arm", type=int, default=60)
    parser.add_argument("--seed", type=int, default=12012)
    parser.add_argument("--max-chars", type=int, default=96_000)
    args = parser.parse_args()

    discovered = discover_labeled_transcripts(args.dataset_root, args.paper_root, args.max_chars)
    records = build_records(discovered, args.n_per_arm, args.seed)
    write_jsonl(args.output, records)

    index = []
    for record in records:
        public_record = {key: value for key, value in record.items() if key != "messages"}
        index.append(public_record)
    write_jsonl(args.index_output, index)

    counts: dict[str, int] = {}
    for record in records:
        key = f"{record['arm']}/{record['ground_truth']}"
        counts[key] = counts.get(key, 0) + 1
    print(json.dumps({"discovered": len(discovered), "records": len(records), "counts": counts}, indent=2))


if __name__ == "__main__":
    main()
