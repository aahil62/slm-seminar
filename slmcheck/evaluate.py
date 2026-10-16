"""Execute every saved sample: hidden correctness, public checks, self-tests and the S4 signature."""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Sequence

from . import config
from .dataset import Problem, Test
from .executor import outputs_equal, run_tests
from .generate import _keys, _repair_tail


def _load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def evaluate(run_dir: Path | str, problems: Sequence[Problem]) -> int:
    """Append one row per sample to exec.jsonl; resumable. Returns rows written this call."""
    run = Path(run_dir)
    pmap = {p.id: p for p in problems}
    selftests = {(r["cfg"], r["problem_id"]): [Test(t["input"], t["output"], pmap[r["problem_id"]].testtype)
                                               for t in r["tests"]]
                 for r in _load(run / "selftests.jsonl") if r["problem_id"] in pmap}
    exec_p = run / "exec.jsonl"
    _repair_tail(exec_p)
    done = _keys(exec_p, ("cfg", "problem_id", "sample_idx"))
    cache: dict[tuple, dict] = {}
    written = 0
    with open(exec_p, "a", encoding="utf-8") as ef, \
            open(run / "progress.log", "a", encoding="utf-8") as logf:
        samples = [s for s in _load(run / "samples.jsonl") if s["problem_id"] in pmap]
        for n, s in enumerate(samples, 1):
            key = (s["cfg"], s["problem_id"], s["sample_idx"])
            if key in done:
                continue
            p = pmap[s["problem_id"]]
            st = selftests.get((s["cfg"], p.id), [])
            ckey = (hashlib.sha256(s["code"].encode()).hexdigest(), p.id, s["cfg"])
            if ckey not in cache:
                cache[ckey] = _execute(s["code"], p, st)
            row = {"cfg": s["cfg"], "tier": s.get("tier", "slm"), "problem_id": p.id, "sample_idx": s["sample_idx"],
                   "difficulty": p.difficulty, "empty": not s["code"].strip(), **cache[ckey]}
            ef.write(json.dumps(row) + "\n")
            ef.flush()
            done.add(key)
            written += 1
            if written % 50 == 0:
                logf.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} evaluate {n}/{len(samples)}\n")
                logf.flush()
    return written


def _execute(code: str, p: Problem, selftests: list[Test]) -> dict:
    timeout = config.TIMEOUT_HARD_S if p.difficulty == "hard" else config.TIMEOUT_S
    if not code.strip():
        return {"hidden_pass": False, "public": [False] * len(p.public),
                "self": [False] * len(selftests), "sig": None}
    probe = list(p.public) + list(selftests)
    ran = run_tests(code, probe, p.func_name, timeout, expect_outputs=False)
    got = [r.got if r.status == "ran" else None for r in ran]
    public = [outputs_equal(t.output, g, t.testtype) for t, g in zip(p.public, got)]
    self_ = [outputs_equal(t.output, g, t.testtype) for t, g in zip(selftests, got[len(p.public):])]
    sig = None
    if any(g is not None for g in got):
        norm = [" ".join(g.split()) if g is not None else "<none>" for g in got]
        sig = hashlib.sha256(json.dumps(norm).encode()).hexdigest()[:16]
    hidden = all(public) and bool(public)
    if hidden and p.private:
        hidden = all(r.passed for r in run_tests(code, p.private, p.func_name, timeout,
                                                 stop_on_fail=True))
    return {"hidden_pass": hidden, "public": public, "self": self_, "sig": sig}
