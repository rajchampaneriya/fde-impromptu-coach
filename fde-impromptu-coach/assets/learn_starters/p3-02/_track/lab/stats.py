"""Paired comparisons for saved runs. YOU fill this in (project 3, step 2); the CI gate uses compare()."""
from __future__ import annotations

import math
from typing import Dict, List, Tuple

import numpy as np


def table(a: List[bool], b: List[bool]) -> Dict[str, int]:
    """The 2 × 2 table for two runs on the same cases, in the same order."""
    return {"both": sum(x and y for x, y in zip(a, b)), "only_a": sum(x and not y for x, y in zip(a, b)),
            "only_b": sum(y and not x for x, y in zip(a, b)), "neither": sum(not x and not y for x, y in zip(a, b))}


def bootstrap(a: List[bool], b: List[bool], n: int = 2000, seed: int = 0) -> Tuple[float, float, float]:
    """Mean of b − a and its 95% bootstrap interval: (mean, low, high)."""
    # TODO: d = np.array(b, float) - np.array(a, float); resample d with replacement n times (np.random.default_rng);
    #       return d.mean(), the 2.5th and the 97.5th percentile of the resampled means
    raise NotImplementedError


def mcnemar(a: List[bool], b: List[bool]) -> float:
    """Two-sided exact McNemar p-value from the two disagreement cells."""
    t = table(a, b)
    k, n = min(t["only_a"], t["only_b"]), t["only_a"] + t["only_b"]
    if n == 0:
        return 1.0
    # TODO: p = 2 * P(X <= k) for X ~ Binomial(n, 0.5), capped at 1.0 (math.comb helps)
    raise NotImplementedError


def compare(a: List[bool], b: List[bool]) -> Dict[str, float]:
    mean, low, high = bootstrap(a, b)
    return {"difference": mean, "low": low, "high": high, "p_value": mcnemar(a, b)}
