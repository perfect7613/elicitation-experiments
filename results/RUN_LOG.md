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

## Phase 2 prospective replication

Date: 2026-09-04 (Asia/Kolkata)

The Phase 2 preregistration, source indexes, and deterministic manifest builder were
committed and pushed at `f1ed23c` before either Phase 2 generation run.

### Decision-point resampling

```bash
.venv/bin/modal run modal_app.py \
  --manifest data/actor_resample_manifest.jsonl \
  --output results/raw/phase2-actor-resample.jsonl \
  --max-new-tokens 384 \
  --no-enable-thinking
```

- Modal app: <https://modal.com/apps/ameymuke252003/main/ap-faE1kuK5joISIsoZaNlInx>
- 270/270 completed; 269 stop, one length-limited
- 54 source prefixes × five matched replicates
- prompt/completion tokens: 1,588,900 / 28,796
- batch elapsed time: 214.139 seconds
- SHA-256: `f25c91377de8500d9ed4795f2ae99c0951ccea3f9e0126cc8ff2b41803447c76`

The strict two-coder result was 18/270 workarounds across 11 source prefixes, which
passed the prospectively frozen ≥5% and ≥3-prefix recreation gate.

### Paired multi-seed elicitation

```bash
.venv/bin/modal run modal_app.py \
  --manifest data/phase2_manifest.jsonl \
  --output results/raw/phase2-paired-elicitation.jsonl \
  --no-enable-thinking
```

- Modal app: <https://modal.com/apps/ameymuke252003/main/ap-KEhzjX6bQ0Ax8rth1NK6pt>
- 630/630 completed; 619 stop, 11 length-limited
- exact frozen-manifest coverage; 60 source trajectories
- prompt/completion tokens: 9,277,962 / 79,613
- batch elapsed time: 497.217 seconds
- SHA-256: `d8df0b26b63a22fa2177408043bd9c837bc727698dc1e8ab75fd67e985f8c8d7`

Both runs recorded one NVIDIA H100 80GB HBM3, Python 3.12.1, torch
2.13.0+cu130, CUDA 13.0, transformers 5.5.3, vLLM 0.28.0, BF16, and the pinned
Qwen revision `40c069824f4251a91eefaf281ebe4c544efd3e18`.

### Phase 2 coding deviations and retries

A Claude Sonnet CLI call was attempted, but Claude Code reported an expired OAuth
session and returned no labels. Phase 2 therefore used two independent response-only
masked Codex CLI passes: `gpt-5.6-luna` and `gpt-5.6-sol`, high reasoning effort,
isolated temporary working directories, and read-only sandboxes. This evaluator
substitution is disclosed; the aliases are not immutable snapshots. The recorded
CLIs were Codex CLI 0.147.0 and Claude Code 2.1.259.

The exact first-pass Codex invocations were:

```bash
.venv/bin/python scripts/run_phase2_codex_judge.py --packets results/labels/phase2_actor --prompt prompts/phase2_actor_judge.txt --kind actor --model gpt-5.6-luna --output-dir results/labels/phase2_actor/codex_luna
.venv/bin/python scripts/run_phase2_codex_judge.py --packets results/labels/phase2_actor --prompt prompts/phase2_actor_judge.txt --kind actor --model gpt-5.6-sol --output-dir results/labels/phase2_actor/codex_sol
.venv/bin/python scripts/run_phase2_codex_judge.py --packets results/labels/phase2_elicitation --prompt prompts/phase2_elicitation_judge.txt --kind elicitation --model gpt-5.6-luna --output-dir results/labels/phase2_elicitation/codex_luna
.venv/bin/python scripts/run_phase2_codex_judge.py --packets results/labels/phase2_elicitation --prompt prompts/phase2_elicitation_judge.txt --kind elicitation --model gpt-5.6-sol --output-dir results/labels/phase2_elicitation/codex_sol
```

The actor-Luna technical retry reran the two affected 30-row batches; only the three
invalid first-pass IDs were selected by the merge:

```bash
.venv/bin/python scripts/run_phase2_codex_judge.py --packets results/labels/phase2_actor --prompt prompts/phase2_actor_judge.txt prompts/exact_evidence_retry.txt --kind actor --model gpt-5.6-luna --output-dir results/labels/phase2_actor/codex_luna_retry --start 6 --end 7
.venv/bin/python scripts/merge_phase2_judgments.py --packets results/labels/phase2_actor --primary results/labels/phase2_actor/codex_luna --retry results/labels/phase2_actor/codex_luna_retry --kind actor --output results/labels/phase2_actor/codex_luna_merged.json
.venv/bin/python scripts/merge_phase2_judgments.py --packets results/labels/phase2_actor --primary results/labels/phase2_actor/codex_sol --kind actor --output results/labels/phase2_actor/codex_sol_merged.json
```

For elicitation, invalid-ID-only packets were generated and rerun. Seven Luna and
four Sol retries failed exact-span validation again, so those IDs received a second
technical retry. The exact commands were:

```bash
.venv/bin/python scripts/prepare_phase2_retry_packets.py --packets results/labels/phase2_elicitation --judgments results/labels/phase2_elicitation/codex_luna --kind elicitation --output-dir results/labels/phase2_elicitation/luna_retry_packets
.venv/bin/python scripts/run_phase2_codex_judge.py --packets results/labels/phase2_elicitation/luna_retry_packets --prompt prompts/phase2_elicitation_judge.txt prompts/exact_evidence_retry.txt --kind elicitation --model gpt-5.6-luna --output-dir results/labels/phase2_elicitation/codex_luna_retry
.venv/bin/python scripts/prepare_phase2_retry_packets.py --packets results/labels/phase2_elicitation/luna_retry_packets --judgments results/labels/phase2_elicitation/codex_luna_retry --kind elicitation --output-dir results/labels/phase2_elicitation/luna_retry2_packets
.venv/bin/python scripts/run_phase2_codex_judge.py --packets results/labels/phase2_elicitation/luna_retry2_packets --prompt prompts/phase2_elicitation_judge.txt prompts/exact_evidence_retry.txt --kind elicitation --model gpt-5.6-luna --output-dir results/labels/phase2_elicitation/codex_luna_retry2
.venv/bin/python scripts/merge_phase2_judgments.py --packets results/labels/phase2_elicitation/luna_retry_packets --primary results/labels/phase2_elicitation/codex_luna_retry --retry results/labels/phase2_elicitation/codex_luna_retry2 --kind elicitation --output results/labels/phase2_elicitation/codex_luna_retry_merged/batch_01.judgments.json
.venv/bin/python scripts/merge_phase2_judgments.py --packets results/labels/phase2_elicitation --primary results/labels/phase2_elicitation/codex_luna --retry results/labels/phase2_elicitation/codex_luna_retry_merged --kind elicitation --output results/labels/phase2_elicitation/codex_luna_merged.json
.venv/bin/python scripts/prepare_phase2_retry_packets.py --packets results/labels/phase2_elicitation --judgments results/labels/phase2_elicitation/codex_sol --kind elicitation --output-dir results/labels/phase2_elicitation/sol_retry_packets
.venv/bin/python scripts/run_phase2_codex_judge.py --packets results/labels/phase2_elicitation/sol_retry_packets --prompt prompts/phase2_elicitation_judge.txt prompts/exact_evidence_retry.txt --kind elicitation --model gpt-5.6-sol --output-dir results/labels/phase2_elicitation/codex_sol_retry
.venv/bin/python scripts/prepare_phase2_retry_packets.py --packets results/labels/phase2_elicitation/sol_retry_packets --judgments results/labels/phase2_elicitation/codex_sol_retry --kind elicitation --output-dir results/labels/phase2_elicitation/sol_retry2_packets
.venv/bin/python scripts/run_phase2_codex_judge.py --packets results/labels/phase2_elicitation/sol_retry2_packets --prompt prompts/phase2_elicitation_judge.txt prompts/exact_evidence_retry.txt --kind elicitation --model gpt-5.6-sol --output-dir results/labels/phase2_elicitation/codex_sol_retry2
.venv/bin/python scripts/merge_phase2_judgments.py --packets results/labels/phase2_elicitation/sol_retry_packets --primary results/labels/phase2_elicitation/codex_sol_retry --retry results/labels/phase2_elicitation/codex_sol_retry2 --kind elicitation --output results/labels/phase2_elicitation/codex_sol_retry_merged/batch_01.judgments.json
.venv/bin/python scripts/merge_phase2_judgments.py --packets results/labels/phase2_elicitation --primary results/labels/phase2_elicitation/codex_sol --retry results/labels/phase2_elicitation/codex_sol_retry_merged --kind elicitation --output results/labels/phase2_elicitation/codex_sol_merged.json
```

The deterministic validator rejected judgments whose evidence was not an exact
substring. Three actor-Luna, 16 elicitation-Luna, and 10 elicitation-Sol first-pass
items failed. The two affected actor batches were rerun, but only rejected IDs were
selected during merge. Elicitation reruns contained rejected IDs only. Seven Luna
and four Sol elicitation retries needed a second retry with the saved exact-copy
instruction. Merge provenance records which pass supplied each final label. No
label was manually overwritten, and all rejected and retry outputs remain in
`results/labels/`.

The detailed coder prompts were written after generation, before masked coding.
This is an outcome-definition degree of freedom beyond the preregistered category
summaries and is reported as such.

The human-audit packet has 295 rows: all liberal positives, all coder disagreements,
15 deterministic negatives per actor truth stratum, and 10 per elicitation
arm/truth cell. An initial packet incorrectly exposed arm, truth, source, replicate,
and AI judgments. A hostile review caught this before publication. The generator
was fixed to emit a six-column blinded packet and a separate metadata key. Human
columns remain intentionally blank.

The exact final analysis invocation was:

```bash
.venv/bin/python scripts/analyze_phase2.py \
  --actor-raw results/raw/phase2-actor-resample.jsonl \
  --actor-key results/labels/phase2_actor/key.jsonl \
  --actor-luna results/labels/phase2_actor/codex_luna_merged.json \
  --actor-sol results/labels/phase2_actor/codex_sol_merged.json \
  --elicitation-raw results/raw/phase2-paired-elicitation.jsonl \
  --elicitation-key results/labels/phase2_elicitation/key.jsonl \
  --elicitation-luna results/labels/phase2_elicitation/codex_luna_merged.json \
  --elicitation-sol results/labels/phase2_elicitation/codex_sol_merged.json \
  --output-dir results/analysis/phase2
```

Final derived-artifact hashes after the source-deduplication bootstrap fix:

During pre-publication testing, a new unit test found that the initial analysis
script listed each paired source twice (once per arm) in the bootstrap pool. Point
estimates were unchanged, but the first intervals were too narrow. The code was
fixed to deduplicate source IDs, all derived files and figures were regenerated,
and only the corrected intervals are reported. No commit containing the incorrect
intervals was pushed.

| Artifact | SHA-256 |
|---|---|
| actor Luna merged labels | `5337f959a191035900c667b1a52e2493372e1e5b6bbba7e97ef77878f5e0fa5e` |
| actor Sol merged labels | `9071c305e1c7ed3aa9b2e31b34a8aa9e1302861b237da15d8f70c484d0d9f5f8` |
| elicitation Luna merged labels | `b3d61ce9495dbff6496eb23305b4a0dbfd68f5c94c80429652cdf747d6de99fd` |
| elicitation Sol merged labels | `2f209c9f07fdf326c968d59e5476d105f4ef40d9b3acef273b46cd968f10119f` |
| Phase 2 summary | `dfae53822067b044d22ba4e92d7d66b992c321b62d081585fe94d937364d310e` |
| blinded human-audit packet | `c90b703f4fcf531b71541dc62b062197f578f9ec8497f782880fe0a97004f499` |
| human-audit metadata key | `b7d332513151e6a3bbe1d015ec419ce7b0469a5c31f127e3aa2b476b7debacfa` |
| replicate-rate table | `57f96299cc99c95794f3dc3b14c8a9fa8d7a39e894799f9b9b8ebba5c13b92d1` |
| deterministic examples | `aab8ee8633b5243e47f3d3519f6c12d0d1bdc2fa5d4d29218af9665ec120a70e` |
