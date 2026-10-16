"""Verification gates a run must pass before its results are used. Each gate records PASS / FAIL / FLAG
checks with evidence in run_dir/verify_state.json and renders VERIFICATION_REPORT.md.

FAIL  = something is broken; stop and repair before continuing.
FLAG  = suspicious result; investigate and explain in the report, do not silently ignore.
"""
from __future__ import annotations

import ast
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Callable, Optional, Sequence

from . import config, prompts
from .backends import Backend, make_backend
from .config import ModelConfig
from .dataset import Problem, load_problems
from .evaluate import _load
from .executor import run_tests
from .generate import load_all, seed_for
from .select import by_problem, select

FIXTURES = Path(__file__).with_name("fixtures")


class Gate:
    def __init__(self, stage: str):
        self.stage, self.checks = stage, []

    def check(self, name: str, ok: bool, evidence: str, flag_only: bool = False) -> bool:
        status = "PASS" if ok else ("FLAG" if flag_only else "FAIL")
        self.checks.append({"name": name, "status": status, "evidence": evidence})
        return ok

    @property
    def status(self) -> str:
        st = {c["status"] for c in self.checks}
        return "FAIL" if "FAIL" in st else ("FLAG" if "FLAG" in st else "PASS")


def _save(run_dir: Path, gate: Gate) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    state_p = run_dir / "verify_state.json"
    state = json.loads(state_p.read_text(encoding="utf-8")) if state_p.exists() else {}
    state[gate.stage] = {"status": gate.status, "at": time.strftime("%Y-%m-%d %H:%M:%S"),
                         "checks": gate.checks}
    state_p.write_text(json.dumps(state, indent=1), encoding="utf-8")
    lines = ["# Verification report", "",
             "Gates run by `python -m slmcheck verify`. FAIL = broken, must be repaired. "
             "FLAG = suspicious, must be investigated and explained below.", ""]
    for stage in ["env", "data", "exec", "backend", "post"]:
        if stage not in state:
            lines += [f"## {stage}: NOT RUN", ""]
            continue
        s = state[stage]
        lines += [f"## {stage}: {s['status']} ({s['at']})", "", "| check | status | evidence |",
                  "|---|---|---|"]
        lines += [f"| {c['name']} | {c['status']} | {c['evidence'].replace('|', '/')} |"
                  for c in s["checks"]]
        lines.append("")
    notes = run_dir / "VERIFICATION_NOTES.md"
    lines += ["## Run notes (investigations, repairs, deviations)", "",
              notes.read_text(encoding="utf-8") if notes.exists() else "_none recorded_", ""]
    (run_dir / "VERIFICATION_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def gate_env(run_dir: Path, cfgs: Sequence[ModelConfig]) -> Gate:
    g = Gate("env")
    g.check("python>=3.11", sys.version_info >= (3, 11), sys.version.split()[0])
    tags = []
    try:
        with urllib.request.urlopen(config.OLLAMA_URL + "/api/tags", timeout=10) as r:
            tags = [m["name"] for m in json.loads(r.read()).get("models", [])]
        g.check("ollama reachable", True, f"{len(tags)} local models")
    except OSError as e:
        g.check("ollama reachable", False, f"{config.OLLAMA_URL}: {e}")
    for cfg in cfgs:
        if cfg.provider == "ollama":
            have = cfg.model in tags or f"{cfg.model}:latest" in tags
            g.check(f"model pulled: {cfg.model}", have, "present" if have else f"run: ollama pull {cfg.model}")
    smi = shutil.which("nvidia-smi")
    if smi:
        out = subprocess.run([smi, "--query-gpu=name,memory.total,memory.free,driver_version",
                              "--format=csv,noheader"], capture_output=True, text=True).stdout.strip()
        g.check("nvidia GPU visible", bool(out), out or "no output")
    else:
        g.check("nvidia GPU visible", False, "nvidia-smi not on PATH", flag_only=True)
    if any(c.provider == "groq" for c in cfgs):
        g.check("GROQ_API_KEY set", bool(os.environ.get("GROQ_API_KEY")), "value not shown")
    free_gb = shutil.disk_usage(run_dir.resolve().anchor or ".").free / 1e9
    g.check("disk free >= 20 GB", free_gb >= 20, f"{free_gb:.0f} GB free", flag_only=True)
    _save(run_dir, g)
    return g


def gate_data(run_dir: Path, problems: Sequence[Problem], min_problems: int = 150) -> Gate:
    g = Gate("data")
    g.check(f"problem count >= {min_problems}", len(problems) >= min_problems, f"{len(problems)} problems")
    bad = [p.id for p in problems if not p.public or not p.private]
    g.check("every problem has public and private tests", not bad, f"missing: {bad[:10]}")
    diff = {d: sum(p.difficulty == d for p in problems) for d in ("easy", "medium", "hard")}
    g.check("difficulty mix", all(diff.values()), json.dumps(diff), flag_only=True)
    tt = {t: sum(p.testtype == t for p in problems) for t in ("stdin", "functional")}
    g.check("test types", sum(tt.values()) == len(problems), json.dumps(tt))
    nofn = [p.id for p in problems if p.testtype == "functional" and not p.func_name]
    g.check("functional problems have func_name", not nofn, f"missing: {nofn[:10]}")
    leaks = []
    for p in problems:
        text = "\n".join(m["content"] for m in prompts.codegen_messages(p) + prompts.selftest_messages(p))
        pub = {t.input.strip() for t in p.public}
        if any(len(t.input.strip()) >= 12 and t.input.strip() not in pub and t.input.strip() in text
               for t in p.private):
            leaks.append(p.id)
    g.check("no private test input appears in any prompt", not leaks, f"leaks: {leaks[:10]}")
    dates = sorted(p.contest_date for p in problems)
    g.check(f"all dates >= {config.SINCE}", not dates or dates[0] >= config.SINCE,
            f"{dates[0] if dates else '-'} .. {dates[-1] if dates else '-'}")
    _save(run_dir, g)
    return g


def gate_exec(run_dir: Path) -> Gate:
    g = Gate("exec")
    sols = json.loads((FIXTURES / "solutions.json").read_text(encoding="utf-8"))
    for p in load_problems(FIXTURES / "problems.jsonl"):
        tests = p.public + p.private
        good = run_tests(sols[p.id]["good"], tests, p.func_name, config.TIMEOUT_S)
        g.check(f"reference passes: {p.id}", all(r.passed for r in good), str([r.status for r in good]))
        bad = run_tests(sols[p.id]["bad"], tests, p.func_name, 2.0, stop_on_fail=True)
        g.check(f"wrong solution fails: {p.id}", not all(r.passed for r in bad), str([r.status for r in bad]))
    t0 = time.time()
    r = run_tests("while True:\n    pass\n", load_problems(FIXTURES / "problems.jsonl")[0].public, None, 1.0)
    g.check("timeout kills runaway code", r[0].status == "timeout" and time.time() - t0 < 10,
            f"{r[0].status} in {time.time() - t0:.1f}s")
    _save(run_dir, g)
    return g


def gate_backend(run_dir: Path, problems: Sequence[Problem], cfgs: Sequence[ModelConfig],
                 backend_factory: Callable[[ModelConfig], Backend] = make_backend) -> Gate:
    g = Gate("backend")
    probe = list(problems)[:3]
    for cfg in cfgs:
        try:
            b = backend_factory(cfg)
            parsed, toks, secs = 0, 0, 0.0
            for p in probe:
                c = b.complete(prompts.codegen_messages(p), 0.0, 1.0, seed_for(p.id, 0), cfg.max_tokens)
                code = prompts.extract_code(c.text)
                toks, secs = toks + c.completion_tokens, secs + c.wall_s
                try:
                    ast.parse(code)
                    parsed += bool(code.strip())
                except SyntaxError:
                    pass
            g.check(f"{cfg.name} returns parsable code", parsed >= 1,
                    f"{parsed}/{len(probe)} parsable; {toks} tokens in {secs:.1f}s "
                    f"({toks / secs if secs else 0:.1f} tok/s)")
        except Exception as e:  # noqa: BLE001 - report any backend failure as evidence
            g.check(f"{cfg.name} returns parsable code", False, f"{type(e).__name__}: {str(e)[:200]}")
    _save(run_dir, g)
    return g


def gate_post(run_dir: Path, problems: Sequence[Problem], cfgs: Sequence[ModelConfig],
              backend_factory: Optional[Callable[[ModelConfig], Backend]] = make_backend) -> Gate:
    g = Gate("post")
    samples = load_all(run_dir, "samples")
    pids = {p.id for p in problems}
    keys = [(s["cfg"], s["problem_id"], s["sample_idx"]) for s in samples]
    g.check("no duplicate sample keys", len(keys) == len(set(keys)), f"{len(keys) - len(set(keys))} duplicates")
    for cfg in cfgs:
        mine = [s for s in samples if s["cfg"] == cfg.name and s["problem_id"] in pids]
        want = len(pids) * cfg.k
        g.check(f"{cfg.name}: sample count", len(mine) == want, f"{len(mine)}/{want}")
        if mine:
            empty = sum(1 for s in mine if not s["code"].strip()) / len(mine)
            errs = sum(1 for s in mine if s.get("error"))
            g.check(f"{cfg.name}: empty extractions < 5%", empty < 0.05, f"{empty:.1%} empty, {errs} errors")
    slm_cfgs = [c for c in cfgs if c.tier == "slm"]
    st = load_all(run_dir, "selftests")
    for cfg in slm_cfgs:
        mine = [r for r in st if r["cfg"] == cfg.name]
        usable = sum(1 for r in mine if r["tests"])
        g.check(f"{cfg.name}: self-tests usable for >= 50% of problems", usable >= 0.5 * len(pids),
                f"{usable}/{len(pids)}", flag_only=True)
    if backend_factory and slm_cfgs:
        cfg = slm_cfgs[0]
        b, pmap, same, tried = backend_factory(cfg), {p.id: p for p in problems}, 0, 0
        for s in [s for s in samples if s["cfg"] == cfg.name and s["sample_idx"] == 0][:3]:
            c = b.complete(prompts.codegen_messages(pmap[s["problem_id"]]), 0.0, 1.0, s["seed"], cfg.max_tokens)
            tried += 1
            same += prompts.extract_code(c.text) == s["code"]
        g.check(f"{cfg.name}: greedy sample reproducible", same == tried, f"{same}/{tried} identical",
                flag_only=True)
    ex = _load(run_dir / "exec.jsonl")
    if ex:
        g.check("every sample executed", len(ex) >= len([s for s in samples if s["problem_id"] in pids]),
                f"{len(ex)} exec rows / {len(samples)} samples")
        pmap = {p.id: p for p in problems}
        s0 = {}
        for cfg in cfgs:
            rows = by_problem(ex, cfg.name)
            s0[cfg.name] = {pid: select(r, "S0").correct for pid, r in rows.items()}
        slm_best = max((sum(v.values()) / max(1, len(v)) for c, v in s0.items()
                        if c in {x.name for x in slm_cfgs}), default=0.0)
        easy_any = any(ok for c in slm_cfgs for pid, ok in s0.get(c.name, {}).items()
                       if pmap[pid].difficulty == "easy")
        g.check("some SLM solves at least one easy problem", easy_any, "harness or prompt problem if not",
                flag_only=True)
        for cfg in [c for c in cfgs if c.tier == "llm"]:
            v = s0.get(cfg.name, {})
            acc = sum(v.values()) / max(1, len(v))
            g.check(f"{cfg.name}: accuracy >= best SLM S0", acc >= slm_best,
                    f"{acc:.3f} vs {slm_best:.3f}", flag_only=True)
            g.check(f"{cfg.name}: accuracy > 0.2 (else suspect harness)", acc > 0.2, f"{acc:.3f}",
                    flag_only=True)
            for tt in ("stdin", "functional"):
                sub = [ok for pid, ok in v.items() if pmap[pid].testtype == tt]
                if sub:
                    g.check(f"{cfg.name}: solves some {tt} problems", any(sub),
                            f"{sum(sub)}/{len(sub)} (0 means the {tt} harness is likely broken)")
    _save(run_dir, g)
    return g
