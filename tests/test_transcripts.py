from pathlib import Path

from hughes_forensics.transcripts import LabeledTranscript, build_records, normalize_messages


def fixture(source_id: str, truth: str) -> LabeledTranscript:
    return LabeledTranscript(
        source_id=source_id,
        timestamp="t",
        run=source_id,
        ground_truth=truth,
        bypass_methods=("--no-verify",) if truth == "guilty" else (),
        explanation="fixture",
        message_path=Path("messages.json"),
        messages=[{"role": "user", "content": "task"}],
        transcript_sha256="0" * 64,
        truncated_history=False,
    )


def test_normalization_excludes_reasoning_and_flattens_tools() -> None:
    raw = [
        {"role": "assistant", "content": "I will inspect.", "reasoning": "private", "tool_calls": [{"function": {"name": "execute_command", "arguments": "{\\\"command\\\":\\\"ls\\\"}"}}]},
        {"role": "tool", "content": "file.py", "tool_call_id": "x"},
    ]
    normalized = normalize_messages(raw)
    assert "private" not in str(normalized)
    assert "execute_command" in normalized[0]["content"]
    assert normalized[1]["role"] == "user"


def test_four_arm_counts_and_pairing() -> None:
    transcripts = [fixture(f"g{i}", "guilty") for i in range(4)] + [
        fixture(f"i{i}", "innocent") for i in range(8)
    ]
    records = build_records(transcripts, n_per_arm=4, seed=7)
    assert len(records) == 16
    assert sum(row["arm"] == "D" for row in records) == 4
    assert all(row["ground_truth"] == "innocent" for row in records if row["arm"] == "D")
    for arm in "ABC":
        arm_rows = [row for row in records if row["arm"] == arm]
        assert sum(row["ground_truth"] == "guilty" for row in arm_rows) == 2
        assert sum(row["ground_truth"] == "innocent" for row in arm_rows) == 2

