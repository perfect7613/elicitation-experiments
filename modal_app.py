"""Modal H100 runner for Qwen3-14B transcript-conditioned follow-ups."""

from __future__ import annotations

import json
import platform
import subprocess
import time
from pathlib import Path
from typing import Any

import modal

APP_NAME = "elicitation-experiments"
MODEL_ID = "Qwen/Qwen3-14B"
MODEL_REVISION = "40c069824f4251a91eefaf281ebe4c544efd3e18"
CACHE_DIR = "/cache/huggingface"

app = modal.App(APP_NAME)
cache = modal.Volume.from_name("elicitation-experiments-hf-cache", create_if_missing=True)
image = (
    modal.Image.from_registry("nvidia/cuda:13.0.1-devel-ubuntu22.04", add_python="3.12")
    .entrypoint([])
    .apt_install("git")
    .uv_pip_install(
        "vllm==0.28.0",
        "transformers==5.5.3",
        "huggingface-hub>=0.34",
        extra_options="--torch-backend=cu130",
    )
    .env(
        {
            "HF_HOME": CACHE_DIR,
            "TOKENIZERS_PARALLELISM": "true",
        }
    )
)


def _prompt(
    tokenizer: Any, record: dict[str, Any], enable_thinking: bool = True
) -> tuple[str, int]:
    messages = list(record["messages"])
    if record.get("followup") is not None:
        messages.append({"role": "user", "content": record["followup"]})
    try:
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=enable_thinking,
        )
    except TypeError:
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    token_count = len(tokenizer(text, add_special_tokens=False)["input_ids"])
    return text, token_count


@app.function(
    image=image,
    gpu="H100",
    volumes={CACHE_DIR: cache},
    timeout=4 * 60 * 60,
    scaledown_window=300,
)
def run_batch(
    records: list[dict[str, Any]],
    model_id: str = MODEL_ID,
    model_revision: str = MODEL_REVISION,
    max_model_len: int = 32_768,
    max_new_tokens: int = 512,
    temperature: float = 0.6,
    top_p: float = 0.95,
    enable_thinking: bool = True,
) -> list[dict[str, Any]]:
    import torch
    import transformers
    import vllm
    from transformers import AutoTokenizer
    from vllm import LLM, SamplingParams

    started_at = time.perf_counter()
    gpu_name = subprocess.run(
        ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()
    runtime = {
        "gpu_name": gpu_name,
        "python_version": str(platform.python_version()),
        "torch_version": str(torch.__version__),
        "cuda_version": str(torch.version.cuda),
        "transformers_version": str(transformers.__version__),
        "vllm_version": str(vllm.__version__),
    }
    print(f"Runtime provenance: {json.dumps(runtime, sort_keys=True)}")

    tokenizer = AutoTokenizer.from_pretrained(
        model_id, revision=model_revision, trust_remote_code=False
    )
    prompts: list[str] = []
    prompt_tokens: list[int] = []
    kept: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []

    for record in records:
        prompt, count = _prompt(tokenizer, record, enable_thinking=enable_thinking)
        if count + max_new_tokens > max_model_len:
            rejected.append(
                {
                    "record_id": record["record_id"],
                    "arm": record["arm"],
                    "ground_truth": record["ground_truth"],
                    "status": "rejected_context_too_long",
                    "prompt_tokens": count,
                }
            )
            continue
        prompts.append(prompt)
        prompt_tokens.append(count)
        kept.append(record)

    llm = LLM(
        model=model_id,
        revision=model_revision,
        dtype="bfloat16",
        max_model_len=max_model_len,
        gpu_memory_utilization=0.90,
        max_num_seqs=8,
        enable_prefix_caching=True,
        trust_remote_code=False,
    )
    params = [
        SamplingParams(
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_new_tokens,
            seed=int(record["generation_seed"]),
        )
        for record in kept
    ]
    outputs = llm.generate(prompts, params, use_tqdm=True)
    runtime["batch_elapsed_seconds"] = round(time.perf_counter() - started_at, 3)

    completed: list[dict[str, Any]] = []
    for record, count, output in zip(kept, prompt_tokens, outputs, strict=True):
        choice = output.outputs[0]
        completed.append(
            {
                "record_id": record["record_id"],
                "arm": record["arm"],
                "arm_name": record["arm_name"],
                "ground_truth": record["ground_truth"],
                "followup": record["followup"],
                "generation_seed": record["generation_seed"],
                "source": record["source"],
                "model_id": model_id,
                "model_revision": model_revision,
                "temperature": temperature,
                "top_p": top_p,
                "max_new_tokens": max_new_tokens,
                "enable_thinking": enable_thinking,
                "prompt_tokens": count,
                "completion_tokens": len(choice.token_ids),
                "finish_reason": choice.finish_reason,
                "status": "completed",
                "response": choice.text,
                "runtime": runtime,
            }
        )
    for row in rejected:
        row["runtime"] = runtime
    cache.commit()
    return completed + rejected


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


@app.local_entrypoint()
def main(
    manifest: str = "data/manifest.jsonl",
    output: str = "results/raw/qwen3-14b.jsonl",
    limit: int = 0,
    model_id: str = MODEL_ID,
    max_new_tokens: int = 512,
    enable_thinking: bool = True,
) -> None:
    """Run pending records only, making interrupted launches safely resumable."""
    manifest_path = Path(manifest)
    output_path = Path(output)
    records = _read_jsonl(manifest_path)
    existing = _read_jsonl(output_path) if output_path.exists() else []
    done = {row["record_id"] for row in existing if row.get("status") == "completed"}
    pending = [record for record in records if record["record_id"] not in done]
    if limit > 0:
        pending = pending[:limit]
    if not pending:
        print("No pending records.")
        return
    fresh = run_batch.remote(
        pending,
        model_id=model_id,
        max_new_tokens=max_new_tokens,
        enable_thinking=enable_thinking,
    )
    by_id = {row["record_id"]: row for row in existing}
    by_id.update({row["record_id"]: row for row in fresh})
    merged = [by_id[key] for key in sorted(by_id)]
    _write_jsonl(output_path, merged)
    print(f"Saved {len(fresh)} new rows; {len(merged)} total rows at {output_path}")
