"""Validate blinded AI-judge outputs and apply them to a copy of a label sheet."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sheet", type=Path, required=True)
    parser.add_argument("--judgments", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    with args.sheet.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    judgments: dict[str, dict] = {}
    for path in args.judgments:
        for judgment in json.loads(path.read_text(encoding="utf-8")):
            blind_id = judgment["blind_id"]
            if blind_id in judgments:
                raise ValueError(f"Duplicate judgment for {blind_id}")
            severity = judgment["severity_0_to_4"]
            if not isinstance(severity, int) or severity not in range(5):
                raise ValueError(f"Invalid severity for {blind_id}: {severity!r}")
            if not isinstance(judgment["denial_or_correction"], bool):
                raise TypeError(f"Invalid denial flag for {blind_id}")
            judgments[blind_id] = judgment

    sheet_ids = [row["blind_id"] for row in rows]
    if set(sheet_ids) != set(judgments):
        missing = sorted(set(sheet_ids) - set(judgments))
        extra = sorted(set(judgments) - set(sheet_ids))
        raise ValueError(f"Judgment IDs do not match sheet; missing={missing}, extra={extra}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        for row in rows:
            judgment = judgments[row["blind_id"]]
            row["severity_0_to_4"] = judgment["severity_0_to_4"]
            row["denial_or_correction"] = str(judgment["denial_or_correction"]).lower()
            row["notes"] = judgment["notes"]
            writer.writerow(row)

    print(f"Applied {len(rows)} validated judgments to {args.output}")


if __name__ == "__main__":
    main()
