"""Paired statistics (stdlib port of the exact McNemar / Holm / Wilson / bootstrap helpers)."""
from __future__ import annotations

import math
import random
from typing import Optional, Sequence

Z95 = 1.959963984540054


def exact_mcnemar(only_a: int, only_b: int) -> float:
    """Two-sided exact McNemar p-value from the discordant counts."""
    n = only_a + only_b
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, i) for i in range(min(only_a, only_b) + 1)) / 2 ** n
    return min(1.0, 2.0 * tail)


def holm(p_values: Sequence[float]) -> list[float]:
    order = sorted(range(len(p_values)), key=lambda i: p_values[i])
    adjusted, running, total = [0.0] * len(p_values), 0.0, len(p_values)
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (total - rank) * p_values[i]))
        adjusted[i] = running
    return adjusted


def wilson(successes: int, total: int, z: float = Z95) -> tuple[float, float]:
    if total == 0:
        return (0.0, 1.0)
    p = successes / total
    den = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / den
    half = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / den
    return (max(0.0, centre - half), min(1.0, centre + half))


def bootstrap_mean_ci(values: Sequence[float], resamples: int = 10_000, seed: int = 20261016,
                      alpha: float = 0.05) -> tuple[float, float]:
    """Percentile bootstrap over problems for a mean (e.g. a paired difference)."""
    if not values:
        return (float("nan"), float("nan"))
    rng, n = random.Random(seed), len(values)
    means = sorted(sum(values[rng.randrange(n)] for _ in range(n)) / n for _ in range(resamples))
    return (means[int(alpha / 2 * resamples)], means[int((1 - alpha / 2) * resamples) - 1])


def gap_recovered(acc_s: float, acc_s0: float, acc_llm: float) -> Optional[float]:
    """Share of the SLM-to-LLM gap closed by a strategy; None when there is no gap."""
    den = acc_llm - acc_s0
    return None if den <= 0 else (acc_s - acc_s0) / den
