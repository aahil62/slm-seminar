"""N2: local-first escalation. Keep the SLM answer when the realistic check accepts it,
otherwise use the cloud LLM's answer."""
from __future__ import annotations

from typing import Sequence

from . import config
from .select import by_problem, select


def random_baseline(local_ok: Sequence[bool], llm_ok: Sequence[bool], rate: float) -> float:
    n = len(local_ok)
    return ((1 - rate) * sum(local_ok) + rate * sum(llm_ok)) / n


def oracle_baseline(local_ok: Sequence[bool], llm_ok: Sequence[bool], rate: float) -> float:
    n = len(local_ok)
    gain = sum(1 for lo, lm in zip(local_ok, llm_ok) if not lo and lm)
    return (sum(local_ok) + min(round(rate * n), gain)) / n


def cascade_curve(slm_rows: Sequence[dict], llm_rows: Sequence[dict], strategy: str,
                  taus: Sequence[float] = config.TAUS) -> list[dict]:
    """slm_rows/llm_rows: exec rows of one SLM config and one LLM config."""
    slm = by_problem(slm_rows, slm_rows[0]["cfg"])
    llm = by_problem(llm_rows, llm_rows[0]["cfg"])
    pids = sorted(set(slm) & set(llm))
    llm_ok = [bool(min(llm[p], key=lambda r: r["sample_idx"])["hidden_pass"]) for p in pids]
    s0_ok = [select(slm[p], "S0").correct for p in pids]
    n = len(pids)
    base = {"slm": slm_rows[0]["cfg"], "llm": llm_rows[0]["cfg"], "n": n}
    points = [
        {**base, "strategy": "all-local", "tau": None, "escalation_rate": 0.0,
         "accuracy": sum(s0_ok) / n, "random_acc": None, "oracle_acc": None},
        {**base, "strategy": "all-cloud", "tau": None, "escalation_rate": 1.0,
         "accuracy": sum(llm_ok) / n, "random_acc": None, "oracle_acc": None},
    ]
    for tau in (taus if strategy == "S3" else [None]):
        picks = [select(slm[p], strategy, tau if tau is not None else config.PRIMARY_TAU)
                 for p in pids]
        local_ok = [pk.correct for pk in picks]
        final = [pk.correct if pk.accepted else lo for pk, lo in zip(picks, llm_ok)]
        rate = sum(1 for pk in picks if not pk.accepted) / n
        points.append({**base, "strategy": strategy, "tau": tau, "escalation_rate": rate,
                       "accuracy": sum(final) / n,
                       "random_acc": random_baseline(local_ok, llm_ok, rate),
                       "oracle_acc": oracle_baseline(local_ok, llm_ok, rate)})
    return points
