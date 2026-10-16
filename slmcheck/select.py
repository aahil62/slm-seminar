"""Answer-selection strategies S0-S5 (design section 6) and per-config N1 metrics."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Optional, Sequence

from . import config

STRATEGIES = ["S0", "S1", "S2", "S3", "S4", "S5"]
DIFFICULTIES = ["easy", "medium", "hard", "all"]


@dataclass(frozen=True)
class Pick:
    sample_idx: int
    accepted: Optional[bool]
    correct: bool
    fail_kind: Optional[str] = None


def _public_ok(r: dict) -> bool:
    return bool(r["public"]) and all(r["public"])


def _pick(r: dict, accepted: Optional[bool]) -> Pick:
    return Pick(r["sample_idx"], accepted, bool(r["hidden_pass"]), r.get("fail_kind"))


def select(rows: Sequence[dict], strategy: str, tau: float = config.PRIMARY_TAU) -> Pick:
    """rows: all samples of one config for one problem."""
    rows = sorted(rows, key=lambda r: r["sample_idx"])
    if strategy == "S0":
        return _pick(rows[0], None)
    if strategy == "S1":
        return _pick(next((r for r in rows if r["hidden_pass"]), rows[0]), None)
    if strategy == "S2":
        r = next((r for r in rows if _public_ok(r)), None)
        return _pick(r, True) if r else _pick(rows[0], False)
    if strategy == "S3":
        if not any(r["self"] for r in rows):
            return select(rows, "S2")
        score = lambda r: sum(r["self"]) / len(r["self"]) if r["self"] else 0.0
        best = min(rows, key=lambda r: (-score(r), not _public_ok(r), r["sample_idx"]))
        return _pick(best, score(best) >= tau)
    if strategy == "S4":
        groups = defaultdict(list)
        for r in rows:
            if r.get("sig"):
                groups[r["sig"]].append(r)
        if not groups:
            return _pick(rows[0], False)
        rep = lambda g: min(g, key=lambda r: (not _public_ok(r), r["sample_idx"]))
        best = min(groups.values(), key=lambda g: (-len(g), not _public_ok(rep(g)),
                                                   rep(g)["sample_idx"]))
        return _pick(rep(best), len(best) > len(rows) / 2)
    if strategy == "S5":
        # combined check: among samples passing the examples, take the largest agreeing group;
        # accept only if that group is a majority of all k samples
        groups = defaultdict(list)
        for r in rows:
            if _public_ok(r) and r.get("sig"):
                groups[r["sig"]].append(r)
        if not groups:
            return _pick(rows[0], False)
        best = min(groups.values(), key=lambda g: (-len(g), g[0]["sample_idx"]))
        return _pick(best[0], len(best) > len(rows) / 2)
    raise ValueError(f"unknown strategy {strategy}")


def by_problem(rows: Sequence[dict], cfg: str) -> dict[str, list[dict]]:
    out = defaultdict(list)
    for r in rows:
        if r["cfg"] == cfg:
            out[r["problem_id"]].append(r)
    return dict(out)


def per_config_table(exec_rows: Sequence[dict], cfg: str,
                     tau: float = config.PRIMARY_TAU) -> list[dict]:
    probs = by_problem(exec_rows, cfg)
    table = []
    for s in STRATEGIES:
        picks = [(rows[0]["difficulty"], select(rows, s, tau)) for rows in probs.values()]
        for d in DIFFICULTIES:
            sub = [p for diff, p in picks if d == "all" or diff == d]
            if not sub:
                continue
            acc = [p for p in sub if p.accepted]
            table.append({
                "cfg": cfg, "strategy": s, "tau": tau if s == "S3" else None, "difficulty": d,
                "n": len(sub), "accuracy": sum(p.correct for p in sub) / len(sub),
                "accept_rate": None if s in ("S0", "S1") else len(acc) / len(sub),
                "false_pass_rate": (sum(not p.correct for p in acc) / len(acc)) if acc else None,
            })
    return table
