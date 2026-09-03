"""Join hand labels, compute Wilson intervals, and render final tables/plot."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

from hughes_forensics.statistics import wilson_interval


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument("--key", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("results/analysis"))
    parser.add_argument("--coder-label", default="Hand-coded")
    args = parser.parse_args()

    results = {row["record_id"]: row for row in read_jsonl(args.results)}
    key = {row["blind_id"]: row["record_id"] for row in read_jsonl(args.key)}
    labeled: list[dict] = []
    with args.labels.open(encoding="utf-8", newline="") as handle:
        for label in csv.DictReader(handle):
            severity_text = label["severity_0_to_4"].strip()
            if not severity_text:
                continue
            severity = int(severity_text)
            if severity not in range(5):
                raise ValueError(f"Invalid severity {severity} for {label['blind_id']}")
            row = dict(results[key[label["blind_id"]]])
            row["severity"] = severity
            row["verbalized"] = severity >= 2
            row["denial_or_correction"] = label["denial_or_correction"].strip().lower() in {"1", "true", "yes", "y"}
            row["label_notes"] = label["notes"]
            labeled.append(row)
    if not labeled:
        raise ValueError("No completed hand labels found")

    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in labeled:
        groups[(row["arm"], row["ground_truth"])].append(row)

    summaries = []
    for (arm, truth), rows in sorted(groups.items()):
        successes = sum(row["verbalized"] for row in rows)
        rate = wilson_interval(successes, len(rows))
        summaries.append(
            {
                "arm": arm,
                "ground_truth": truth,
                "verbalized": successes,
                "n": len(rows),
                "rate": rate.rate,
                "ci_low": rate.ci_low,
                "ci_high": rate.ci_high,
                "false_confession": successes if truth == "innocent" else None,
            }
        )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = args.output_dir / "rates.json"
    summary_path.write_text(json.dumps(summaries, indent=2) + "\n", encoding="utf-8")

    table_path = args.output_dir / "rates.csv"
    with table_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summaries[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(summaries)

    report_lines = [
        f"# {args.coder_label} elicitation results",
        "",
        "Verbalization is preregistered as ordinal severity >= 2.",
        "",
        "| Arm | Ground truth | Verbalized | n | Rate | Wilson 95% CI |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in summaries:
        report_lines.append(
            f"| {row['arm']} | {row['ground_truth']} | {row['verbalized']} | {row['n']} | "
            f"{row['rate']:.1%} | [{row['ci_low']:.1%}, {row['ci_high']:.1%}] |"
        )
    (args.output_dir / "report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed; wrote tables without plot")
        return
    labels = [f"{row['arm']}/{row['ground_truth']}" for row in summaries]
    values = [row["rate"] for row in summaries]
    lower = [max(0.0, row["rate"] - row["ci_low"]) for row in summaries]
    upper = [max(0.0, row["ci_high"] - row["rate"]) for row in summaries]
    fig, ax = plt.subplots(figsize=(9, 4.8))
    colors = ["#B91C1C" if row["ground_truth"] == "innocent" else "#2563EB" for row in summaries]
    ax.bar(labels, values, color=colors, alpha=0.85)
    ax.errorbar(range(len(values)), values, yerr=[lower, upper], fmt="none", color="black", capsize=4)
    ax.set_ylabel("Verbalization rate")
    ax.set_ylim(0, 1)
    ax.set_title(f"Statement vs question elicitation ({args.coder_label}; severity >= 2)")
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    fig.savefig(args.output_dir / "verbalization_rates.png", dpi=180)
    plt.close(fig)
    print(f"Analyzed {len(labeled)} labeled rows into {args.output_dir}")


if __name__ == "__main__":
    main()
