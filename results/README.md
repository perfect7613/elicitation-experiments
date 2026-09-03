# Results

See [`../REPORT.md`](../REPORT.md) for the evidence-led write-up and `RUN_LOG.md`
for the full operational audit trail, including failed launches.

- `raw/` contains the excluded smoke output and both 240-response H100 runs.
- `labels/` retains blank sheets, blinded batch inputs, raw Claude judgments, and
  labeled copies. These are AI-coded labels, not human labels.
- `analysis/preregistered_claude_ai_coded/` reports the thinking-mode response field.
- `analysis/no_thinking_*` contains each coder and strict/liberal sensitivity views.
- `analysis/summary/` contains run integrity, runtime provenance, deterministic
  examples, and the two headline figures.

Do not commit a Modal token, HF token, full generated input manifest, or environment
file.
