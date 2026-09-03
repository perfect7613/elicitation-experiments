"""Dependency-free binary-rate summaries used by the analysis script."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Rate:
    successes: int
    total: int
    rate: float
    ci_low: float
    ci_high: float


def wilson_interval(successes: int, total: int, z: float = 1.959963984540054) -> Rate:
    if total <= 0:
        raise ValueError("total must be positive")
    if successes < 0 or successes > total:
        raise ValueError("successes must be between zero and total")
    p = successes / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * total)) / total) / denominator
    return Rate(successes, total, p, max(0.0, center - margin), min(1.0, center + margin))

