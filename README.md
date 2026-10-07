# llm-sizer

**LLM VRAM calculator + cheapest AWS GPU picker.** Size DeepSeek-R1, Llama 70B, Qwen, Mixtral, and other inference workloads before you launch vLLM — then get a single-node instance recommendation and monthly on-demand cost.

[![CI](https://github.com/saheb26/llm-sizer/actions/workflows/ci.yml/badge.svg)](https://github.com/saheb26/llm-sizer/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/llm-sizer.svg)](https://pypi.org/project/llm-sizer/)
[![PyPI downloads](https://img.shields.io/pypi/dm/llm-sizer.svg)](https://pypi.org/project/llm-sizer/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![JSON for agents](https://img.shields.io/badge/output-JSON%20for%20AI%20agents-brightgreen.svg)](AGENTS.md)

![llm-sizer demo: DeepSeek-R1 q4 32k maps to p4de.24xlarge](docs/demo.gif)

Stop guessing whether Llama 3 70B fits on a `g5.12xlarge`. `llm-sizer` adds **weight VRAM + KV cache VRAM**, maps the total to the cheapest AWS GPU that actually fits, and prints a terminal table (or JSON for agents).

```bash
pip install llm-sizer
llm-sizer --model deepseek-r1 --quant q4 --concurrent-users 8 --context 32k
```

## Why this exists

Most GPU “rules of thumb” only count model weights. Production vLLM crashes usually come from **KV cache** growing with context length and concurrent users:

```
weights     = params × bytes_per_param
kv_cache    = 2 × layers × hidden_size × context × users × bytes_per_param
total_vram  = weights + kv_cache
```

`fp16`/`bf16` = 2 bytes, `q8` = 1 byte, `q4` = 0.5 bytes.

## Quick start

```bash
pip install llm-sizer

llm-sizer --model llama-3-70b --quant fp16 --concurrent-users 4 --context 8k
llm-sizer --model qwen2.5-72b --quant q8 --concurrent-users 16 --context 32k
llm-sizer --list-models
```

From source:

```bash
git clone https://github.com/saheb26/llm-sizer.git
cd llm-sizer
pip install -e .
```

### AI agents / scripts

Machine-readable JSON on stdout (pretty tables stay on the human path):

```bash
llm-sizer --model llama-3-70b --quant q4 --context 32k --concurrent-users 8 --json
```

```json
{
  "tool": "llm-sizer",
  "model": "llama-3-70b",
  "vram_gb": { "weights": 32.88, "kv_cache": 160.0, "total": 192.88 },
  "recommendation": {
    "fits_single_node": true,
    "instance": "g6e.48xlarge",
    "gpu": "8x L40S",
    "vram_gb": 384,
    "usd_per_month": 21694.32
  }
}
```

Cursor / Claude / Codex: read [`AGENTS.md`](AGENTS.md) and [`llms.txt`](llms.txt).

## Example

```text
DeepSeek-R1  |  Q4  |  32k  |  8 users
Weights 312.46 GB  ·  KV cache 106.75 GB  ·  Total 419.21 GB
Recommended: p4de.24xlarge (8x A100 80GB, 640 GB)  ·  $29,495/mo
```

| Workload | Total VRAM | Cheapest fit | Est. monthly |
| --- | --- | --- | --- |
| Llama 3 8B · q4 · 8k · 1 user | 4.74 GB | `g4dn.xlarge` | ~$379 |
| Llama 3 70B · fp16 · 8k · 4 users | 211.50 GB | `g6e.48xlarge` | ~$21,694 |
| DeepSeek-R1 · q4 · 32k · 8 users | 419.21 GB | `p4de.24xlarge` | ~$29,495 |

## CLI

| Flag | Short | Meaning | Example |
| --- | --- | --- | --- |
| `--model` | `-m` | Model id or alias | `deepseek-r1`, `llama-70b` |
| `--quant` | `-q` | `fp16`, `bf16`, `q8`, `q4` | `q4` |
| `--concurrent-users` | `-u` | Simultaneous sequences | `8` |
| `--context` | `-c` | Window (`8k`, `32k`, `128k`, or tokens) | `32k` |
| `--json` | | Agent-friendly JSON | |
| `--list-models` | | Catalog dump | `--list-models --json` |

## Built-in models

DeepSeek-R1 / V3 · Llama 3 / 3.1 / 3.3 (8B, 70B, 405B) · Mistral 7B · Mixtral 8x7B / 8x22B · Qwen2.5 (7B–72B) · Gemma 2 · Phi-4

Aliases accepted: `llama70b`, `llama-70b`, `deepseek`, `r1`, `qwen-72b`, `mixtral`.

## AWS catalog

Cheapest **us-east-1 on-demand** instance whose GPU memory covers total VRAM:

`g4dn` · `g5` · `g6` · `g6e` · `p4d` · `p4de` · `p5` · `p5en`

Prices are approximate public list rates and will drift. Treat them as planning numbers, not invoices.

## Deploy the architecture

Stop guessing AWS instances and managing vLLM crashes. Deploy this exact architecture securely inside your VPC with one click using [CounselNode](https://counselnode.com).

## Keywords

LLM VRAM calculator, vLLM GPU memory, KV cache size, DeepSeek-R1 VRAM, Llama 70B AWS instance, cheapest GPU for LLM inference, H100 A100 L40S sizing, AI agent CLI.

## License

MIT. Issues and PRs welcome — model cards, newer GPU SKUs, and extra aliases help everyone.
