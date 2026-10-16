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
from .generate import _keys, _repair_tail, load_all


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
                 for r in load_all(run, "selftests") if r["problem_id"] in pmap}
    exec_p = run / "exec.jsonl"
    _repair_tail(exec_p)
    done = _keys(exec_p, ("cfg", "problem_id", "sample_idx"))
    cache: dict[tuple, dict] = {}
    written = 0
    with open(exec_p, "a", encoding="utf-8") as ef, \
            open(run / "progress.log", "a", encoding="utf-8") as logf:
        samples = [s for s in load_all(run, "samples") if s["problem_id"] in pmap]
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


def _probe_scripts(tests: list[Test]) -> list[Test]:
    """For assert-style tests: scripts that print the value under test, so agreement between
    samples (S4/S5) can be measured on outputs rather than on pass/fail."""
    import ast
    out = []
    for t in tests:
        try:
            mod = ast.parse(t.input)
        except SyntaxError:
            continue
        setup = [n for n in mod.body if isinstance(n, (ast.Import, ast.ImportFrom))]
        for node in mod.body:
            if isinstance(node, ast.Assert) and isinstance(node.test, ast.Compare):
                expr = ast.unparse(node.test.left)
                pre = "".join(ast.unparse(n) + "\n" for n in setup)
                out.append(Test(pre + f"print(repr({expr}))", "", "script"))
    return out


_KIND = {"fail": "wrong_answer", "error": "runtime_error", "timeout": "timeout"}


def _execute(code: str, p: Problem, selftests: list[Test]) -> dict:
    """fail_kind: why hidden grading failed (wrong_answer / runtime_error / timeout / empty)."""
    timeout = config.TIMEOUT_HARD_S if p.difficulty == "hard" else config.TIMEOUT_S
    if not code.strip():
        return {"hidden_pass": False, "fail_kind": "empty", "public": [False] * len(p.public),
                "self": [False] * len(selftests), "sig": None}
    checks = list(p.public) + list(selftests)
    extra = _probe_scripts(checks) if p.testtype == "script" else []
    ran = run_tests(code, checks + extra, p.func_name, timeout, expect_outputs=False)
    got = [r.got if r.status == "ran" else None for r in ran]
    public = [outputs_equal(t.output, g, t.testtype) for t, g in zip(p.public, got)]
    self_ = [outputs_equal(t.output, g, t.testtype) for t, g in zip(selftests, got[len(p.public):])]
    sig_got = got[len(checks):] if extra else got
    sig = None
    if any(g is not None for g in sig_got):
        norm = [" ".join(g.split()) if g is not None else "<none>" for g in sig_got]
        sig = hashlib.sha256(json.dumps(norm).encode()).hexdigest()[:16]
    fail_kind = None
    bad_public = next((r for r, ok in zip(ran, public) if not ok), None)
    if bad_public is not None or not public:
        fail_kind = _KIND.get(bad_public.status if bad_public else "fail", "wrong_answer")
    elif p.private:
        bad = next((r for r in run_tests(code, p.private, p.func_name, timeout, stop_on_fail=True)
                    if not r.passed), None)
        if bad is not None:
            fail_kind = _KIND.get(bad.status, "wrong_answer")
    return {"hidden_pass": fail_kind is None, "fail_kind": fail_kind, "public": public,
            "self": self_, "sig": sig}
