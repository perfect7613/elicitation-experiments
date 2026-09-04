# Results

See [`../PHASE2_REPORT.md`](../PHASE2_REPORT.md) for the prospective replication,
[`../REPORT.md`](../REPORT.md) for Phase 1, and `RUN_LOG.md` for the full operational
audit trail, including failed launches.

- `raw/` contains the excluded smoke output and both 240-response H100 runs.
- `labels/` retains blank sheets, blinded batch inputs, raw Claude judgments, and
  labeled copies. These are AI-coded labels, not human labels.
- `analysis/preregistered_claude_ai_coded/` reports the thinking-mode response field.
- `analysis/no_thinking_*` contains each coder and strict/liberal sensitivity views.
- `analysis/summary/` contains run integrity, runtime provenance, deterministic
  examples, and the two headline figures.
- `raw/phase2-*` contains the 270-response actor check and 630-response paired run.
- `labels/phase2_*` retains response-only packets, both Codex coding passes, rejected
  exact-span outputs, retries, merged labels, and per-ID merge provenance.
- `analysis/phase2/` contains source-bootstrap results, disagreements, figures,
  complete replicate rates, a 295-row blinded human-audit packet, and its separate
  metadata key. Do not open the key while coding the packet.

Do not commit a Modal token, HF token, full generated input manifest, or environment
file.
