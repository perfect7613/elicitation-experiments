# Data artifacts

- `source_index.jsonl` is the committed 240-record design and provenance index. It excludes transcript bodies.
- `manifest.jsonl` is generated locally from the public source repositories and is intentionally ignored because it embeds about 15 MB of transcript text.

The index pins source revisions and records transcript SHA-256 hashes, arm allocation, follow-up text, published workaround labels, and whether visible history was truncated.

