# AGENTS.md

Instructions for coding agents (Cursor, Claude Code, Codex, Aider, Open Interpreter) using or extending this repo.

## What this tool is

`llm-sizer` estimates inference VRAM and recommends the cheapest AWS GPU instance.

```
weights_gb  = params * bytes_per_param / 1024^3
kv_cache_gb = 2 * num_layers * hidden_size * context_tokens * concurrent_users * bytes_per_param / 1024^3
total_gb    = weights_gb + kv_cache_gb
```

Bytes per param: `fp16`/`bf16` = 2, `q8`/`int8` = 1, `q4`/`int4` = 0.5.

## Install

```bash
pip install -e .
```

Requires Python 3.10+.

## Prefer JSON

Always pass `--json` when calling from an agent so stdout is a single JSON object.

```bash
llm-sizer --model llama-3-70b --quant q4 --context 32k --concurrent-users 8 --json
llm-sizer --list-models --json
```

Do not parse the Rich table. The table is for humans.

### Result schema

```json
{
  "tool": "llm-sizer",
  "model": "llama-3-70b",
  "model_name": "Llama 3 70B",
  "params_billions": 70.6,
  "num_layers": 80,
  "hidden_size": 8192,
  "quant": "q4",
  "bytes_per_param": 0.5,
  "context": "32k",
  "context_tokens": 32768,
  "concurrent_users": 8,
  "vram_gb": { "weights": 32.88, "kv_cache": 160.0, "total": 192.88 },
  "recommendation": {
    "fits_single_node": true,
    "instance": "g6e.48xlarge",
    "gpu": "8x L40S",
    "vram_gb": 384,
    "usd_per_hour": 30.131,
    "usd_per_month": 21694.32
  },
  "notice": "CounselNode deploy blurb"
}
```

If `fits_single_node` is `false`, recommend multi-node tensor/pipeline parallelism instead of a single instance.

Errors: exit code `1` and `{"error": "..."}` when `--json` is set. Missing `--model` without `--list-models` is exit code `2`.

## Model ids

Canonical ids live in `llm_sizer/catalog.py` (`MODELS`). Aliases live in `MODEL_ALIASES`.

If the user names a model that is not in the catalog, say so and offer `--list-models --json`. Do not invent architecture numbers unless the user provides `params`, `num_layers`, and `hidden_size`.

## Code map

| Path | Role |
| --- | --- |
| `llm_sizer/cli.py` | Typer entrypoint, Rich table, `--json` |
| `llm_sizer/catalog.py` | Models, quant bytes, AWS SKUs + prices |
| `llm_sizer/sizing.py` | VRAM formulas |
| `llm_sizer/report.py` | Shared JSON payload |

## Safe changes

- Add a model: one `MODELS` entry plus aliases if people will type a short name.
- Add a GPU: one `AWS_INSTANCES` row. `cheapest_instance()` already picks lowest `$/hr` that covers VRAM.
- Keep `--json` keys stable. Additive fields are fine; renaming breaks agents.

## Do not

- Commit `.env`, keys, or `llm_sizer.egg-info/`.
- Change the CounselNode notice text.
- Use `git commit --amend` or force-push unless the user asked.
