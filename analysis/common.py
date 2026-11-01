"""Shared loaders for the journal-paper analyses.

Everything here reads the frozen result bundle (bundle/<bench>/raw) and never writes to it.
Selection rules are imported from the experiment package (slmcheck.select) so the paper uses
exactly the same S0-S5 definitions as the run itself.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from slmcheck.select import select  # noqa: E402  (read-only reuse)

OUT = REPO / "analysis" / "out"
FIG = REPO / "analysis" / "figures"
BENCH_DIR = {"lcb": REPO / "bundle" / "livecodebench", "mbpp": REPO / "bundle" / "mbppplus"}

SLMS = ["qwen2.5-coder-1.5b", "qwen2.5-coder-7b", "deepseek-coder-6.7b",
        "qwen3-4b-nothink", "qwen3-4b-think"]
MULTI = SLMS[:4]  # k = 5 configs; the thinking config has k = 1
LLMS = ["gpt-oss-120b", "deepseek-v3.1"]
REAL = ["S2", "S3", "S4", "S5"]
SHORT = {"qwen2.5-coder-1.5b": "QC-1.5B", "qwen2.5-coder-7b": "QC-7B",
         "deepseek-coder-6.7b": "DSC-6.7B", "qwen3-4b-nothink": "Q3-4B",
         "qwen3-4b-think": "Q3-4B-T", "gpt-oss-120b": "GPT-OSS-120B",
         "deepseek-v3.1": "DeepSeek-V3.1"}


def jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load(bench: str):
    raw = BENCH_DIR[bench] / "raw"
    exec_rows = jsonl(raw / "exec.jsonl")
    problems = {p["id"]: p for p in jsonl(raw / "problems.jsonl")}
    samples = {}
    for path in sorted(raw.glob("samples__*.jsonl")):
        for s in jsonl(path):
            samples[(s["cfg"], s["problem_id"], int(s["sample_idx"]))] = s
    by = defaultdict(lambda: defaultdict(list))  # cfg -> pid -> rows
    for r in exec_rows:
        by[r["cfg"]][r["problem_id"]].append(r)
    return exec_rows, problems, samples, by


def present_llms(by) -> list[str]:
    return [m for m in LLMS if m in by and len(by[m]) > 0]


def llm_ok(by, llm: str) -> dict[str, bool]:
    return {p: bool(min(rows, key=lambda r: r["sample_idx"])["hidden_pass"])
            for p, rows in by[llm].items()}


def write_csv(name: str, rows: list[dict]) -> None:
    import csv
    OUT.mkdir(parents=True, exist_ok=True)
    keys = list(dict.fromkeys(k for r in rows for k in r)) or ["empty"]
    with open(OUT / name, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()})


__all__ = ["select", "load", "present_llms", "llm_ok", "write_csv", "SLMS", "MULTI", "LLMS",
           "REAL", "SHORT", "OUT", "FIG", "BENCH_DIR", "REPO"]
