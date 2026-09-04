"""Create packets only for judgments that fail deterministic schema/evidence checks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from merge_phase2_judgments import load_judgments, load_packets, valid


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packets", type=Path, required=True)
    parser.add_argument("--judgments", type=Path, required=True)
    parser.add_argument("--kind", choices=("actor", "elicitation"), required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    order, responses = load_packets(args.packets)
    judgments = load_judgments(args.judgments)
    invalid = [
        blind_id
        for blind_id in order
        if blind_id not in judgments
        or not valid(judgments[blind_id], responses[blind_id], args.kind)
    ]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    packet = [{"blind_id": blind_id, "response": responses[blind_id]} for blind_id in invalid]
    (args.output_dir / "batch_01.json").write_text(
        json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Prepared {len(packet)} invalid or missing judgments for retry")


if __name__ == "__main__":
    main()
