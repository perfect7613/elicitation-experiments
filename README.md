# Elicitation Experiments

Reproducible question-vs-statement elicitation on frozen agent transcripts, with an explicit false-confession control.

**Completed results:** read [REPORT.md](REPORT.md). The short version is that the
bracketing statement was the strongest elicitor in a small blinded sample, while a
false incriminating statement produced coder-sensitive false confessions. The report
also documents a preregistered thinking-mode measurement failure, negative results,
exact prompts, raw outputs, failed launches, and limitations.

The package uses published Pre-commit Hook rollouts and workaround labels, branches them with Qwen3-14B on a Modal H100, creates a blinded hand-labeling sheet, and reports Wilson 95% confidence intervals. See [PREREGISTRATION.md](PREREGISTRATION.md) before changing prompts or sampling.

## 1. Clone the two public inputs

```bash
git clone --depth 1 https://huggingface.co/datasets/Model-Forensics/model-forensics ../model-forensics-data
git clone --depth 1 https://github.com/gkroiz/model_forensics_paper.git ../model-forensics-paper
git -C ../model-forensics-data fetch --depth 1 origin e9aa97a7aac835b56b67e28746429d57730b3bdb
git -C ../model-forensics-data checkout e9aa97a7aac835b56b67e28746429d57730b3bdb
git -C ../model-forensics-paper fetch --depth 1 origin abb5fac45f19e91d8356b2f9cc63284cfd8f1bde
git -C ../model-forensics-paper checkout abb5fac45f19e91d8356b2f9cc63284cfd8f1bde
```

The HF repository is about 3.8 GB and contains many small files.

## 2. Set up locally

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev,analysis,modal]'
pytest -q
```

## 3. Build the frozen manifest

```bash
python scripts/prepare_manifest.py \
  --dataset-root ../model-forensics-data \
  --paper-root ../model-forensics-paper \
  --output data/manifest.jsonl \
  --index-output data/source_index.jsonl
```

Expected design: 240 rows total; A/B/C each have 30 guilty + 30 innocent, while D has 60 innocent. `data/manifest.jsonl` is ignored because it embeds full transcripts. `data/source_index.jsonl` is safe to commit and records prompts, labels, hashes, and provenance without transcript bodies.

## 4. Authenticate Modal

```bash
modal setup
modal token info
modal profile current
```

Do not paste or commit a token. Qwen3-14B is public, so the runner does not require an HF secret by default. If Hub rate limits require one, add a Modal secret named `huggingface-secret` and attach it to `run_batch` rather than hard-coding credentials.

## 5. H100 smoke test

The smoke test is resumable and runs only two records:

```bash
modal run modal_app.py --manifest data/manifest.jsonl --output results/raw/smoke.jsonl --limit 2 --max-new-tokens 128
```

Verify that both rows have `status=completed`, sensible prompt/completion token counts, and non-empty responses. The first run builds the vLLM image and downloads the model into the persistent Modal Volume; later runs reuse it.

## 6. Full run

```bash
modal run modal_app.py --manifest data/manifest.jsonl --output results/raw/qwen3-14b.jsonl
```

The completed study also ran a post-hoc non-thinking control after the thinking-mode
sanity check failed:

```bash
modal run modal_app.py \
  --manifest data/manifest.jsonl \
  --output results/raw/qwen3-14b-no-thinking.jsonl \
  --no-enable-thinking
```

Rerun the same command after an interruption. Completed `record_id` values are skipped and the output is merged deterministically. Contexts that exceed the fixed 32,768-token budget are recorded as `rejected_context_too_long` rather than silently truncated at inference time.

The job requests one H100, uses BF16 Qwen3-14B at revision `40c069824f4251a91eefaf281ebe4c544efd3e18`, uses vLLM 0.28.0 in a CUDA 13.0.1/Python 3.12 image, caps vLLM at eight concurrent sequences, and has a four-hour hard timeout. With only 240 short completions, normal runtime should be far below that ceiling after the image/model cache is warm. Check current Modal pricing before launch.

## 7. Blindly hand-label 60

```bash
python scripts/make_label_sheet.py \
  --results results/raw/qwen3-14b.jsonl \
  --output results/labels/blinded_60.csv
```

Fill `severity_0_to_4`, `denial_or_correction`, and `notes` without opening the generated key. The CSV deliberately hides arm, ground truth, and source run. Use the frozen codebook in `PREREGISTRATION.md`.

## 8. Analyze

```bash
python scripts/analyze.py \
  --results results/raw/qwen3-14b.jsonl \
  --labels results/labels/blinded_60.csv \
  --key results/labels/blinded_60_key.jsonl \
  --output-dir results/analysis
```

Outputs:

- `rates.csv` and `rates.json`
- `report.md` with counts and Wilson 95% CIs
- `verbalization_rates.png`

Commit the raw responses, completed blinded labels, key, and analysis outputs after checking them for accidental secrets. They are intentionally not ignored so the public result can be audited.

Do not describe unlabeled model output as a result. The central result is the guilty/innocent tradeoff, not verbalization rate alone.

## Provenance

- Dataset: <https://huggingface.co/datasets/Model-Forensics/model-forensics>
- Paper/code: <https://github.com/gkroiz/model_forensics_paper>
- Model: <https://huggingface.co/Qwen/Qwen3-14B>

The originally circulated dataset ID `adsingh64/model-forensics` now resolves under `Model-Forensics/model-forensics`.
