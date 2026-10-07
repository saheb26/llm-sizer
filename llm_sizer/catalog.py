"""Known model architectures and AWS GPU instance catalog."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelSpec:
    name: str
    params: float
    num_layers: int
    hidden_size: int


@dataclass(frozen=True)
class AwsGpuInstance:
    name: str
    gpu: str
    vram_gb: float
    usd_per_hour: float

    @property
    def monthly_cost(self) -> float:
        return self.usd_per_hour * 24 * 30


# Architecture numbers follow public model cards / Hugging Face configs.
MODELS: dict[str, ModelSpec] = {
    "deepseek-r1": ModelSpec("DeepSeek-R1", 671e9, 61, 7168),
    "deepseek-v3": ModelSpec("DeepSeek-V3", 671e9, 61, 7168),
    "llama-3-8b": ModelSpec("Llama 3 8B", 8.03e9, 32, 4096),
    "llama-3.1-8b": ModelSpec("Llama 3.1 8B", 8.03e9, 32, 4096),
    "llama-3-70b": ModelSpec("Llama 3 70B", 70.6e9, 80, 8192),
    "llama-3.1-70b": ModelSpec("Llama 3.1 70B", 70.6e9, 80, 8192),
    "llama-3.3-70b": ModelSpec("Llama 3.3 70B", 70.6e9, 80, 8192),
    "llama-3.1-405b": ModelSpec("Llama 3.1 405B", 405e9, 126, 16384),
    "mistral-7b": ModelSpec("Mistral 7B", 7.25e9, 32, 4096),
    "mixtral-8x7b": ModelSpec("Mixtral 8x7B", 46.7e9, 32, 4096),
    "mixtral-8x22b": ModelSpec("Mixtral 8x22B", 141e9, 56, 6144),
    "qwen2.5-7b": ModelSpec("Qwen2.5 7B", 7.62e9, 28, 3584),
    "qwen2.5-14b": ModelSpec("Qwen2.5 14B", 14.8e9, 48, 5120),
    "qwen2.5-32b": ModelSpec("Qwen2.5 32B", 32.5e9, 64, 5120),
    "qwen2.5-72b": ModelSpec("Qwen2.5 72B", 72.7e9, 80, 8192),
    "gemma-2-9b": ModelSpec("Gemma 2 9B", 9.24e9, 42, 3584),
    "gemma-2-27b": ModelSpec("Gemma 2 27B", 27.2e9, 46, 4608),
    "phi-4": ModelSpec("Phi-4", 14.7e9, 40, 5120),
}

# Common agent / chat aliases so "llama 70b" style ids still resolve.
MODEL_ALIASES: dict[str, str] = {
    "deepseek": "deepseek-r1",
    "deepseek-r1-671b": "deepseek-r1",
    "r1": "deepseek-r1",
    "llama3-8b": "llama-3-8b",
    "llama-8b": "llama-3-8b",
    "llama3-70b": "llama-3-70b",
    "llama-70b": "llama-3-70b",
    "llama70b": "llama-3-70b",
    "llama-405b": "llama-3.1-405b",
    "llama3.1-405b": "llama-3.1-405b",
    "mixtral": "mixtral-8x7b",
    "qwen-72b": "qwen2.5-72b",
    "qwen-32b": "qwen2.5-32b",
    "qwen-7b": "qwen2.5-7b",
}

QUANT_BYTES: dict[str, float] = {
    "fp32": 4.0,
    "fp16": 2.0,
    "bf16": 2.0,
    "q8": 1.0,
    "int8": 1.0,
    "q4": 0.5,
    "int4": 0.5,
}

# On-demand prices, us-east-1. Sorted cheapest-first so the first fit wins.
AWS_INSTANCES: tuple[AwsGpuInstance, ...] = (
    AwsGpuInstance("g4dn.xlarge", "1x T4", 16, 0.526),
    AwsGpuInstance("g6.xlarge", "1x L4", 24, 0.805),
    AwsGpuInstance("g5.xlarge", "1x A10G", 24, 1.006),
    AwsGpuInstance("g6e.xlarge", "1x L40S", 48, 1.861),
    AwsGpuInstance("g6.12xlarge", "4x L4", 96, 4.602),
    AwsGpuInstance("g5.12xlarge", "4x A10G", 96, 5.672),
    AwsGpuInstance("g6e.12xlarge", "4x L40S", 192, 10.494),
    AwsGpuInstance("g6.48xlarge", "8x L4", 192, 13.350),
    AwsGpuInstance("g5.48xlarge", "8x A10G", 192, 16.288),
    AwsGpuInstance("g6e.48xlarge", "8x L40S", 384, 30.131),
    AwsGpuInstance("p4d.24xlarge", "8x A100 40GB", 320, 32.773),
    AwsGpuInstance("p4de.24xlarge", "8x A100 80GB", 640, 40.965),
    AwsGpuInstance("p5.48xlarge", "8x H100 80GB", 640, 98.320),
    AwsGpuInstance("p5en.48xlarge", "8x H200 141GB", 1128, 127.890),
)


def resolve_model(name: str) -> ModelSpec:
    key = name.strip().lower().replace(" ", "-")
    key = MODEL_ALIASES.get(key, key)
    if key in MODELS:
        return MODELS[key]
    available = ", ".join(sorted(MODELS))
    raise ValueError(f"Unknown model '{name}'. Choose one of: {available}")


def resolve_quant(name: str) -> float:
    key = name.strip().lower()
    if key in QUANT_BYTES:
        return QUANT_BYTES[key]
    available = ", ".join(sorted(QUANT_BYTES))
    raise ValueError(f"Unknown quant '{name}'. Choose one of: {available}")


def parse_context(value: str) -> int:
    raw = value.strip().lower().replace("_", "").replace(",", "")
    multipliers = {"k": 1024, "m": 1024 * 1024}
    if raw and raw[-1] in multipliers:
        return int(float(raw[:-1]) * multipliers[raw[-1]])
    tokens = int(raw)
    if tokens <= 0:
        raise ValueError("Context length must be a positive token count.")
    return tokens


def cheapest_instance(total_vram_gb: float) -> AwsGpuInstance | None:
    candidates = [inst for inst in AWS_INSTANCES if inst.vram_gb >= total_vram_gb]
    if not candidates:
        return None
    return min(candidates, key=lambda inst: inst.usd_per_hour)
