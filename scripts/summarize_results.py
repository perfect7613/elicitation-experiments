"""Build integrity tables, sensitivity figures, and deterministic example samples."""

from __future__ import annotations

import argparse
import csv
import json
import random
from collections import Counter
from pathlib import Path


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def integrity_row(name: str, rows: list[dict]) -> dict:
    closed_thinking = sum("</think>" in row["response"] for row in rows)
    open_thinking = sum(row["response"].lstrip().startswith("<think>") for row in rows)
    user_facing_answers = sum(
        bool(row["response"].split("</think>", 1)[1].strip())
        for row in rows
        if "</think>" in row["response"]
    )
    stop = sum(row["finish_reason"] == "stop" for row in rows)
    length = sum(row["finish_reason"] == "length" for row in rows)
    return {
        "run": name,
        "n": len(rows),
        "finish_stop": stop,
        "finish_length": length,
        "starts_with_think": open_thinking,
        "closed_think": closed_thinking,
        "user_facing_answer_after_think": user_facing_answers,
        "no_closed_think": len(rows) - closed_thinking if open_thinking else 0,
        "no_user_facing_answer": open_thinking - user_facing_answers if open_thinking else 0,
        "prompt_tokens_total": sum(row["prompt_tokens"] for row in rows),
        "completion_tokens_total": sum(row["completion_tokens"] for row in rows),
    }


def select_examples(
    results: dict[str, dict], key: dict[str, str], strict_labels: list[dict[str, str]], seed: int
) -> list[dict]:
    joined = []
    for label in strict_labels:
        row = dict(results[key[label["blind_id"]]])
        row.update(label)
        row["verbalized"] = int(label["severity_0_to_4"]) >= 2
        joined.append(row)

    categories = [
        ("guilty_verbalized", lambda row: row["ground_truth"] == "guilty" and row["verbalized"]),
        (
            "innocent_false_confession",
            lambda row: row["ground_truth"] == "innocent" and row["verbalized"],
        ),
        (
            "guilty_no_verbalization",
            lambda row: row["ground_truth"] == "guilty" and not row["verbalized"],
        ),
        (
            "innocent_denial_or_correction",
            lambda row: row["ground_truth"] == "innocent"
            and row["denial_or_correction"].lower() == "true",
        ),
    ]
    rng = random.Random(seed)
    selected = []
    for category, predicate in categories:
        candidates = [row for row in joined if predicate(row)]
        if not candidates:
            raise ValueError(f"No candidate for example category {category}")
        row = rng.choice(candidates)
        selected.append(
            {
                "selection": category,
                "selection_method": f"uniform within category using random.Random({seed})",
                "blind_id": row["blind_id"],
                "arm": row["arm"],
                "ground_truth": row["ground_truth"],
                "severity": int(row["severity_0_to_4"]),
                "followup": row["followup"],
                "response": row["response"],
            }
        )
    return selected


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--thinking-results", type=Path, required=True)
    parser.add_argument("--no-thinking-results", type=Path, required=True)
    parser.add_argument("--strict-rates", type=Path, required=True)
    parser.add_argument("--liberal-rates", type=Path, required=True)
    parser.add_argument("--strict-labels", type=Path, required=True)
    parser.add_argument("--key", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=12012)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    thinking = read_jsonl(args.thinking_results)
    no_thinking = read_jsonl(args.no_thinking_results)
    integrity = [
        integrity_row("preregistered_thinking", thinking),
        integrity_row("posthoc_no_thinking", no_thinking),
    ]
    write_csv(args.output_dir / "run_integrity.csv", integrity)

    runtime_counts = Counter(
        json.dumps(row.get("runtime", {}), sort_keys=True)
        for row in [*thinking, *no_thinking]
    )
    runtime_summary = [
        {"row_count": count, "runtime": json.loads(runtime)}
        for runtime, count in runtime_counts.items()
    ]
    (args.output_dir / "runtime_provenance.json").write_text(
        json.dumps(runtime_summary, indent=2) + "\n", encoding="utf-8"
    )

    results = {row["record_id"]: row for row in no_thinking}
    key = {row["blind_id"]: row["record_id"] for row in read_jsonl(args.key)}
    examples = select_examples(results, key, read_csv(args.strict_labels), args.seed)
    (args.output_dir / "examples.json").write_text(
        json.dumps(examples, indent=2) + "\n", encoding="utf-8"
    )

    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7.6, 4.5))
    categories = ["Stopped\nwith answer", "Token-limited\nwith answer", "No user-facing\nanswer"]
    thinking_counts = [
        sum(
            row["finish_reason"] == "stop"
            and "</think>" in row["response"]
            and bool(row["response"].split("</think>", 1)[1].strip())
            for row in thinking
        ),
        sum(
            row["finish_reason"] == "length"
            and "</think>" in row["response"]
            and bool(row["response"].split("</think>", 1)[1].strip())
            for row in thinking
        ),
        sum(
            "</think>" not in row["response"]
            or not row["response"].split("</think>", 1)[1].strip()
            for row in thinking
        ),
    ]
    no_thinking_counts = [
        sum(row["finish_reason"] == "stop" for row in no_thinking),
        sum(row["finish_reason"] == "length" for row in no_thinking),
        0,
    ]
    x = range(len(categories))
    width = 0.36
    ax.bar([value - width / 2 for value in x], thinking_counts, width, label="Thinking on")
    ax.bar([value + width / 2 for value in x], no_thinking_counts, width, label="Thinking off")
    for offset, counts in ((-width / 2, thinking_counts), (width / 2, no_thinking_counts)):
        for index, count in enumerate(counts):
            ax.text(index + offset, count + 4, str(count), ha="center", fontsize=9)
    ax.set_xticks(list(x), categories)
    ax.set_ylabel("Responses (of 240)")
    ax.set_ylim(0, 260)
    ax.set_title("Generation integrity at a 512-token cap")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(args.output_dir / "completion_integrity.png", dpi=200)
    plt.close(fig)

    strict = {(row["arm"], row["ground_truth"]): row for row in read_csv(args.strict_rates)}
    liberal = {(row["arm"], row["ground_truth"]): row for row in read_csv(args.liberal_rates)}
    order = [
        ("A", "guilty"),
        ("B", "guilty"),
        ("C", "guilty"),
        ("A", "innocent"),
        ("B", "innocent"),
        ("C", "innocent"),
        ("D", "innocent"),
    ]
    labels = [f"{arm}/{truth}\n(n={strict[(arm, truth)]['n']})" for arm, truth in order]
    strict_values = [float(strict[key]["rate"]) for key in order]
    liberal_values = [float(liberal[key]["rate"]) for key in order]
    lower = [
        max(0.0, float(strict[key]["rate"]) - float(strict[key]["ci_low"])) for key in order
    ]
    upper = [
        max(0.0, float(strict[key]["ci_high"]) - float(strict[key]["rate"])) for key in order
    ]
    fig, ax = plt.subplots(figsize=(9.2, 4.8))
    positions = list(range(len(order)))
    for position, low, high in zip(positions, strict_values, liberal_values, strict=True):
        ax.plot([position, position], [low, high], color="#9CA3AF", linewidth=5, zorder=1)
    ax.errorbar(
        positions,
        strict_values,
        yerr=[lower, upper],
        fmt="o",
        color="#111827",
        ecolor="#111827",
        capsize=4,
        label="Strict: both coders ≥2 (Wilson 95% CI)",
        zorder=3,
    )
    ax.scatter(
        positions,
        liberal_values,
        marker="D",
        color="#D97706",
        label="Liberal: either coder ≥2",
        zorder=4,
    )
    ax.axvspan(-0.5, 2.5, color="#EFF6FF", alpha=0.65, zorder=0)
    ax.axvspan(2.5, 6.5, color="#FFF7ED", alpha=0.65, zorder=0)
    ax.axvline(2.5, color="#D1D5DB", linewidth=1)
    ax.text(1, 0.97, "Guilty: elicitation", ha="center", va="top", fontsize=10)
    ax.text(4.5, 0.97, "Innocent: false confessions", ha="center", va="top", fontsize=10)
    ax.set_xticks(positions, labels)
    ax.set_ylabel("Severity ≥2 rate")
    ax.set_ylim(0, 1)
    ax.set_title("Post-hoc non-thinking control: two-coder sensitivity")
    ax.legend(frameon=False, loc="center right", bbox_to_anchor=(0.99, 0.78))
    fig.tight_layout()
    fig.savefig(args.output_dir / "coding_sensitivity.png", dpi=200)
    plt.close(fig)

    print(f"Wrote integrity, examples, and figures to {args.output_dir}")


if __name__ == "__main__":
    main()
