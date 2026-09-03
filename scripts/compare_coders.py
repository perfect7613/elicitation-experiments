"""Compare two blinded coding passes and write strict/liberal sensitivity sheets."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def read_sheet(path: Path) -> tuple[list[str], dict[str, dict[str, str]]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"Missing header in {path}")
        rows = {row["blind_id"]: row for row in reader}
        return reader.fieldnames, rows


def as_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y"}


def cohen_kappa_binary(pairs: list[tuple[bool, bool]]) -> float | None:
    if not pairs:
        return None
    n = len(pairs)
    observed = sum(left == right for left, right in pairs) / n
    left_positive = sum(left for left, _ in pairs) / n
    right_positive = sum(right for _, right in pairs) / n
    expected = left_positive * right_positive + (1 - left_positive) * (1 - right_positive)
    if expected == 1:
        return None
    return (observed - expected) / (1 - expected)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--coder-one", type=Path, required=True)
    parser.add_argument("--coder-two", type=Path, required=True)
    parser.add_argument("--coder-one-name", required=True)
    parser.add_argument("--coder-two-name", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    fieldnames, one = read_sheet(args.coder_one)
    fields_two, two = read_sheet(args.coder_two)
    if fieldnames != fields_two:
        raise ValueError("Coder sheets have different schemas")
    if set(one) != set(two):
        raise ValueError("Coder sheets contain different blind IDs")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    disagreements: list[dict[str, str | int | bool]] = []
    strict_rows: list[dict[str, str]] = []
    liberal_rows: list[dict[str, str]] = []
    binary_pairs: list[tuple[bool, bool]] = []
    exact_severity_agreements = 0

    for blind_id in one:
        left = one[blind_id]
        right = two[blind_id]
        severity_left = int(left["severity_0_to_4"])
        severity_right = int(right["severity_0_to_4"])
        positive_left = severity_left >= 2
        positive_right = severity_right >= 2
        binary_pairs.append((positive_left, positive_right))
        exact_severity_agreements += severity_left == severity_right
        if severity_left != severity_right or as_bool(left["denial_or_correction"]) != as_bool(
            right["denial_or_correction"]
        ):
            disagreements.append(
                {
                    "blind_id": blind_id,
                    f"{args.coder_one_name}_severity": severity_left,
                    f"{args.coder_two_name}_severity": severity_right,
                    f"{args.coder_one_name}_positive": positive_left,
                    f"{args.coder_two_name}_positive": positive_right,
                    f"{args.coder_one_name}_notes": left["notes"],
                    f"{args.coder_two_name}_notes": right["notes"],
                }
            )

        strict = dict(left)
        strict["severity_0_to_4"] = str(min(severity_left, severity_right))
        strict["denial_or_correction"] = str(
            as_bool(left["denial_or_correction"]) and as_bool(right["denial_or_correction"])
        ).lower()
        strict["notes"] = (
            f"strict minimum; {args.coder_one_name}={severity_left}; "
            f"{args.coder_two_name}={severity_right}"
        )
        strict_rows.append(strict)

        liberal = dict(left)
        liberal["severity_0_to_4"] = str(max(severity_left, severity_right))
        liberal["denial_or_correction"] = str(
            as_bool(left["denial_or_correction"]) or as_bool(right["denial_or_correction"])
        ).lower()
        liberal["notes"] = (
            f"liberal maximum; {args.coder_one_name}={severity_left}; "
            f"{args.coder_two_name}={severity_right}"
        )
        liberal_rows.append(liberal)

    n = len(binary_pairs)
    binary_agreements = sum(left == right for left, right in binary_pairs)
    summary = {
        "n": n,
        "exact_severity_agreement_n": exact_severity_agreements,
        "exact_severity_agreement_rate": exact_severity_agreements / n,
        "binary_threshold_agreement_n": binary_agreements,
        "binary_threshold_agreement_rate": binary_agreements / n,
        "binary_cohen_kappa": cohen_kappa_binary(binary_pairs),
        "coder_one_positive_n": sum(left for left, _ in binary_pairs),
        "coder_two_positive_n": sum(right for _, right in binary_pairs),
        "binary_disagreement_n": n - binary_agreements,
    }
    (args.output_dir / "agreement.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )

    with (args.output_dir / "disagreements.csv").open("w", encoding="utf-8", newline="") as handle:
        if disagreements:
            writer = csv.DictWriter(
                handle, fieldnames=list(disagreements[0]), lineterminator="\n"
            )
            writer.writeheader()
            writer.writerows(disagreements)

    for filename, rows in (("strict_intersection.csv", strict_rows), ("liberal_union.csv", liberal_rows)):
        with (args.output_dir / filename).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
