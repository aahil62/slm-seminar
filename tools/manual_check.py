"""Independent spot-checks of the harness results (does not use slmcheck.executor).

python -I manual_check.py <run_dir> [n_false=5] [n_true=3] [n_extract=5] [seed=1]
 - extraction: for n_extract random samples per config, raw_text vs code (code must occur in raw_text
   after stripping, must parse, must not contain reasoning text).
 - grading: for n_false random hidden_pass=false rows (non-empty code) re-run the candidate on every
   public+private test with a plain subprocess; the failure must reproduce. For n_true hidden_pass=true
   rows the candidate must pass every test.
Prints a markdown report on stdout.
"""
import ast
import json
import random
import subprocess
import sys
import tempfile
from pathlib import Path

RUN = Path(sys.argv[1])
N_FALSE = int(sys.argv[2]) if len(sys.argv) > 2 else 5
N_TRUE = int(sys.argv[3]) if len(sys.argv) > 3 else 3
N_EXTRACT = int(sys.argv[4]) if len(sys.argv) > 4 else 5
random.seed(int(sys.argv[5]) if len(sys.argv) > 5 else 1)
HEADER = ("from typing import *\nfrom collections import *\nfrom itertools import *\nfrom functools import *\n"
          "from heapq import *\nfrom bisect import *\nfrom math import *\nfrom builtins import *\n"
          "import math, heapq, bisect, itertools, functools, collections, string, re, sys, random\n")


def jl(p):
    return [json.loads(l) for l in Path(p).read_text(encoding="utf-8").splitlines() if l.strip()]


problems = {p["id"]: p for p in jl(RUN / "problems.jsonl")}
samples = {}
for f in sorted(RUN.glob("samples__*.jsonl")):
    for s in jl(f):
        samples[(s["cfg"], s["problem_id"], s["sample_idx"])] = s
ex = jl(RUN / "exec.jsonl") if (RUN / "exec.jsonl").exists() else []


def run_one(code, test, func_name, timeout):
    """Run one test in a fresh interpreter; returns (verdict, detail)."""
    tt = test["testtype"]
    with tempfile.TemporaryDirectory() as d:
        if tt == "stdin":
            Path(d, "c.py").write_text(HEADER + code, encoding="utf-8")
            try:
                r = subprocess.run([sys.executable, "-I", "c.py"], cwd=d, input=test["input"], text=True,
                                   capture_output=True, timeout=timeout, encoding="utf-8")
            except subprocess.TimeoutExpired:
                return "timeout", ""
            if r.returncode != 0:
                return "runtime_error", r.stderr[-200:]
            return ("pass" if r.stdout.split() == test["output"].split() else "wrong_answer"), r.stdout[:100]
        if tt == "functional":
            args = [json.loads(l) for l in test["input"].split("\n") if l.strip()]
            Path(d, "c.py").write_text(
                HEADER + code + f"\nimport json as _j\n_a={args!r}\nprint('@@' + _j.dumps(Solution().{func_name}(*_a)))\n",
                encoding="utf-8")
            try:
                r = subprocess.run([sys.executable, "-I", "c.py"], cwd=d, text=True, capture_output=True,
                                   timeout=timeout, encoding="utf-8")
            except subprocess.TimeoutExpired:
                return "timeout", ""
            if r.returncode != 0:
                return "runtime_error", r.stderr[-200:]
            got = [l for l in r.stdout.splitlines() if l.startswith("@@")]
            if not got:
                return "runtime_error", "no output"
            return ("pass" if json.loads(got[-1][2:]) == json.loads(test["output"]) else "wrong_answer"), got[-1][2:][:100]
        Path(d, "c.py").write_text(HEADER + code + "\n" + test["input"], encoding="utf-8")  # script
        try:
            r = subprocess.run([sys.executable, "-I", "c.py"], cwd=d, text=True, capture_output=True,
                               timeout=timeout, encoding="utf-8")
        except subprocess.TimeoutExpired:
            return "timeout", ""
        return ("pass" if r.returncode == 0 else "fail"), r.stderr[-200:]


def grade(row, tl_scale=1.0):
    p, s = problems[row["problem_id"]], samples[(row["cfg"], row["problem_id"], row["sample_idx"])]
    tests = p["public"] + p["private"]
    timeout = (12.0 if p.get("difficulty") == "hard" else 6.0) * tl_scale
    for i, t in enumerate(tests):
        v, detail = run_one(s["code"], t, p.get("func_name"), timeout)
        if v != "pass":
            return False, f"test {i}/{len(tests)} -> {v} {detail!r}"
    return True, f"all {len(tests)} tests passed"


print(f"# Manual spot-checks for {RUN}\n")
print("## Extraction (raw_text vs code)\n")
cfgs = sorted({k[0] for k in samples})
for cfg in cfgs:
    mine = [s for k, s in samples.items() if k[0] == cfg]
    for s in random.sample(mine, min(N_EXTRACT, len(mine))):
        raw, code = s["raw_text"], s["code"]
        if not code.strip():
            kind = "EMPTY (raw empty: truncated while thinking)" if not raw.strip() else "EMPTY despite raw text"
            print(f"- {cfg} {s['problem_id']}#{s['sample_idx']}: {kind}; completion_tokens={s['completion_tokens']}")
            continue
        try:
            ast.parse(code)
            parse = "parses"
        except SyntaxError as e:
            parse = f"SYNTAX ERROR {e.msg}"
        print(f"- {cfg} {s['problem_id']}#{s['sample_idx']}: in_raw={code.strip() in raw}, {parse}, "
              f"len(code)={len(code)}/len(raw)={len(raw)}, has_think_tag={'<think>' in code or '</think>' in code}")

print("\n## Grading: hidden_pass=false rows re-run independently\n")
bad = [e for e in ex if not e["hidden_pass"] and not e["empty"]]
for e in random.sample(bad, min(N_FALSE, len(bad))):
    ok, detail = grade(e)
    print(f"- {e['cfg']} {e['problem_id']}#{e['sample_idx']} exec says {e['fail_kind']}; manual: "
          f"{'FAILURE NOT REPRODUCED (harness suspect)' if ok else 'failure confirmed'} ({detail})")
print("\n## Grading: hidden_pass=true rows re-run independently\n")
good = [e for e in ex if e["hidden_pass"]]
for e in random.sample(good, min(N_TRUE, len(good))):
    ok, detail = grade(e)
    print(f"- {e['cfg']} {e['problem_id']}#{e['sample_idx']} exec says pass; manual: "
          f"{'pass confirmed' if ok else 'MISMATCH (harness suspect)'} ({detail})")
print(f"\n(pool sizes: {len(bad)} failing non-empty rows, {len(good)} passing rows)")

