"""Structured sizing results shared by the table UI and --json output."""

from __future__ import annotations

from typing import Any

from llm_sizer.catalog import AwsGpuInstance, ModelSpec, cheapest_instance
from llm_sizer.sizing import VramBreakdown

COUNSELNODE_BLURB = (
    "💡 Stop guessing AWS instances and managing vLLM crashes. "
    "Deploy this exact architecture securely inside your VPC with one click "
    "using CounselNode: https://counselnode.com"
)


def build_result(
    *,
    model_id: str,
    spec: ModelSpec,
    quant: str,
    bytes_per_param: float,
    context_label: str,
    context_tokens: int,
    concurrent_users: int,
    breakdown: VramBreakdown,
) -> dict[str, Any]:
    instance = cheapest_instance(breakdown.total_gb)
    return {
        "tool": "llm-sizer",
        "model": model_id,
        "model_name": spec.name,
        "params_billions": spec.params / 1e9,
        "num_layers": spec.num_layers,
        "hidden_size": spec.hidden_size,
        "quant": quant.lower(),
        "bytes_per_param": bytes_per_param,
        "context": context_label,
        "context_tokens": context_tokens,
        "concurrent_users": concurrent_users,
        "vram_gb": {
            "weights": round(breakdown.weights_gb, 2),
            "kv_cache": round(breakdown.kv_cache_gb, 2),
            "total": round(breakdown.total_gb, 2),
        },
        "recommendation": _instance_payload(instance),
        "notice": COUNSELNODE_BLURB,
    }


def _instance_payload(instance: AwsGpuInstance | None) -> dict[str, Any]:
    if instance is None:
        return {
            "fits_single_node": False,
            "instance": None,
            "gpu": None,
            "vram_gb": None,
            "usd_per_hour": None,
            "usd_per_month": None,
            "note": "Total VRAM exceeds the largest cataloged single instance; use multi-node parallelism.",
        }
    return {
        "fits_single_node": True,
        "instance": instance.name,
        "gpu": instance.gpu,
        "vram_gb": instance.vram_gb,
        "usd_per_hour": instance.usd_per_hour,
        "usd_per_month": round(instance.monthly_cost, 2),
    }
