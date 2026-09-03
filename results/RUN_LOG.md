# Experiment run log

Date: 2026-09-03 (Asia/Kolkata)

## Frozen inputs

- Experiment repository starting commit: `914e789`
- Model-Forensics data: `e9aa97a7aac835b56b67e28746429d57730b3bdb`
- Model-Forensics paper/code: `abb5fac45f19e91d8356b2f9cc63284cfd8f1bde`
- Source index SHA-256: `1e43d575ddadda67225010fbd77bd9079bfe2cce990c5320114eaaf83a4ed779`
- Rebuilt manifest SHA-256: `6b7a90a1d98ff1e2999339d57aec815e394770196dfbd63513651025d8c50568`

Manifest construction discovered 1,747 source transcripts and selected 240 records.
The regenerated source index matched the committed index byte for byte. Fifty of
240 selected source histories used the preregistered visible-history truncation;
no generation input was silently truncated at inference time.

## Failed infrastructure attempts

These attempts are part of the experimental record:

1. The original `vllm==0.11.0` image failed dependency resolution because the
   requested xformers wheel was unavailable. It did not allocate an H100 or produce
   inference output.
2. Upgrading to `vllm==0.28.0` while retaining `transformers<5` produced a resolver
   conflict. It did not allocate an H100 or produce inference output.
3. A CUDA 12.9 base image with the current vLLM CUDA 13 wheel reached the remote
   function but failed on missing `libcudart.so.13`. It produced no inference output.
4. A CUDA 13 base image with automatic torch-backend selection installed a CPU
   torch wheel and failed on missing `libtorch_cuda.so`. It produced no inference
   output.
5. The corrected CUDA 13 build generated two smoke responses, but runtime metadata
   initially contained a non-serializable torch version object. Local
   deserialization failed, so those two responses were not persisted. Runtime
   metadata was cast to strings before rerunning. This was an instrumentation loss,
   not a selectively discarded result.

No failed attempt contributed a response to an analysis file.

## Successful Modal runs

### Smoke test

```bash
.venv/bin/modal run modal_app.py --manifest data/manifest.jsonl --output results/raw/smoke.jsonl --limit 2 --max-new-tokens 128
```

- 2/2 completed on `NVIDIA H100 80GB HBM3`
- both reached the 128-token limit inside an unclosed reasoning block
- excluded from outcome analysis
- SHA-256: `05f8e7bd9f1a823cb75e38ee29729ffe40358c661e1ac725d5742c5996077030`

### Preregistered thinking-mode run

```bash
.venv/bin/modal run modal_app.py --manifest data/manifest.jsonl --output results/raw/qwen3-14b.jsonl
```

- Modal app: <https://modal.com/apps/ameymuke252003/main/ap-BpOVbLd3YOqigVb8dddfaX>
- 240/240 completed, all record IDs unique, exact manifest coverage
- 108 stop completions; 132 length-limited completions
- 189 responses contained a non-empty user-facing answer after `</think>`;
  51 did not
- total prompt/completion tokens: 3,681,986 / 110,418
- recorded batch elapsed time: 930.082 seconds, including load/warm-up
- SHA-256: `8df3ab7656388568bc017aaea21c516973092f84a749c9c35ef036faea9cbcbd`

### Post-hoc non-thinking control

```bash
.venv/bin/modal run modal_app.py --manifest data/manifest.jsonl --output results/raw/qwen3-14b-no-thinking.jsonl --no-enable-thinking
```

- Modal app: <https://modal.com/apps/ameymuke252003/main/ap-OYs1nRubs0yPAcgZQAPIf9>
- 240/240 completed, all record IDs unique, exact manifest coverage
- 239 stop completions; one length-limited completion
- no reasoning tags; every response contained direct answer text
- total prompt/completion tokens: 3,682,946 / 28,992
- recorded batch elapsed time: 425.049 seconds, including load/warm-up
- SHA-256: `c612e8b9adf02bfd2d5e4ceb5d25e6fd960544e97e777ab515b87defc46f0fe1`

Both full runs recorded the same environment on every row: H100 80GB HBM3,
Python 3.12.1, torch 2.13.0+cu130, CUDA 13.0, transformers 5.5.3, and vLLM 0.28.0.

## Blinded coding

The preregistration specified hand coding. No human coder was available, so the
actual labels are explicitly named AI-coded and treated as a protocol deviation.

- A monolithic 60-row Claude Sonnet request was stopped after about five minutes
  without output.
- Two 30-row Sonnet batches succeeded for each result mode.
- After a manual audit identified threshold ambiguity, two independently blinded
  Claude Opus batches were run on the post-hoc non-thinking sample.
- The Opus prompt prohibited access to prior judgments, keys, arm labels, ground
  truth, source transcripts, other result files, and git history.
- Sonnet and Opus agreed on 57/60 binary calls and 51/60 exact severity scores.
- A later read-only Opus request for a hostile whole-repository methodology review
  was stopped after several minutes with no output. It supplied no evidence and is
  not represented as an endorsement.

All blank sheets, batch inputs, raw judge JSON, labeled copies, disagreements, and
strict/liberal sensitivity sheets are retained under `results/labels` and
`results/analysis/no_thinking_coder_comparison`.
