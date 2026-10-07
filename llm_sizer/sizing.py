"""VRAM math for model weights and KV cache."""

from __future__ import annotations

from dataclasses import dataclass

from llm_sizer.catalog import ModelSpec


BYTES_PER_GIB = 1024**3


@dataclass(frozen=True)
class VramBreakdown:
    weights_bytes: float
    kv_cache_bytes: float

    @property
    def total_bytes(self) -> float:
        return self.weights_bytes + self.kv_cache_bytes

    @property
    def weights_gb(self) -> float:
        return self.weights_bytes / BYTES_PER_GIB

    @property
    def kv_cache_gb(self) -> float:
        return self.kv_cache_bytes / BYTES_PER_GIB

    @property
    def total_gb(self) -> float:
        return self.total_bytes / BYTES_PER_GIB


def estimate_vram(
    model: ModelSpec,
    bytes_per_param: float,
    context_length: int,
    concurrent_users: int,
) -> VramBreakdown:
    weights = model.params * bytes_per_param
    kv_cache = (
        2
        * model.num_layers
        * model.hidden_size
        * context_length
        * concurrent_users
        * bytes_per_param
    )
    return VramBreakdown(weights_bytes=weights, kv_cache_bytes=kv_cache)
