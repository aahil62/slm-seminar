"""CLI: python -m slmcheck <command> [--run-dir runs/main]. See README.md (Reproducing) for the order."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import zlib
from pathlib import Path

from . import config, dataset, evaluate, generate, report, verify
from .backends import FakeBackend
from .config import ModelConfig

FAKE_CONFIGS = [
    ModelConfig("fake-slm-a", "fake", "fake", k=3),
    ModelConfig("fake-slm-b", "fake", "fake", k=3),
    ModelConfig("fake-llm", "fake", "fake", k=1, tier="llm"),
]


def fake_factory(cfg: ModelConfig):
    """Deterministic stand-in models built from the fixture reference solutions."""
    probs = dataset.load_problems(verify.FIXTURES / "problems.jsonl")
    sols = json.loads((verify.FIXTURES / "solutions.json").read_text(encoding="utf-8"))

    def script(messages, seed):
        text = messages[-1]["content"]
        p = next((p for p in probs if p.content in text), probs[0])
        if "test cases" in text:
            t = p.public[0]
            return "```json\n" + json.dumps([{"input": t.input, "output": t.output},
                                              {"input": t.input, "output": "999"}]) + "\n```"
        idx = seed // 1000
        good = (p.id != "fx_primes") if cfg.tier == "llm" else \
            (idx + zlib.crc32((cfg.name + p.id).encode())) % 2 == 0
        return "```python\n" + sols[p.id]["good" if good else "bad"] + "```"

    return FakeBackend(script)


def _cfgs(args) -> list[ModelConfig]:
    if args.fake:
        return FAKE_CONFIGS
    pool = {"slm": config.SLM_CONFIGS, "llm": config.LLM_CONFIGS}.get(args.tier, config.ALL_CONFIGS)
    return [config.get_config(n) for n in args.cfg] if args.cfg else pool


def _problems(run: Path, fake: bool):
    p = run / "problems.jsonl"
    if fake and not p.exists():
        run.mkdir(parents=True, exist_ok=True)
        shutil.copy2(verify.FIXTURES / "problems.jsonl", p)
    if not p.exists():
        sys.exit(f"{p} missing: run `python -m slmcheck prepare --run-dir {run}` first")
    return dataset.load_problems(p)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="slmcheck")
    ap.add_argument("command", choices=["download", "prepare", "verify", "generate", "evaluate",
                                        "report", "all"])
    ap.add_argument("--run-dir", default="runs/main")
    ap.add_argument("--raw-dir", default="data/raw")
    ap.add_argument("--benchmark", choices=["livecodebench", "mbppplus"], default="livecodebench",
                    help="download/prepare only")
    ap.add_argument("--out", default=None, help="bundle directory (default: <run-dir>/../../bundle)")
    ap.add_argument("--stage", choices=["env", "data", "exec", "backend", "post"])
    ap.add_argument("--cfg", nargs="*", help="config names (default: all)")
    ap.add_argument("--tier", choices=["slm", "llm", "all"], default="all")
    ap.add_argument("--limit", type=int, default=None, help="only the first N problems (smoke runs)")
    ap.add_argument("--min-problems", type=int, default=150)
    ap.add_argument("--fake", action="store_true", help="fixture problems + fake models (pipeline test)")
    a = ap.parse_args(argv)
    run = Path(a.run_dir)
    out = Path(a.out) if a.out else Path("bundle")
    factory = fake_factory if a.fake else None
    cfgs = _cfgs(a)

    if a.command == "download":
        if a.benchmark == "mbppplus":
            print(dataset.download_mbpp(a.raw_dir))
        else:
            print("\n".join(str(p) for p in dataset.download_raw(a.raw_dir)))
        return 0
    if a.command == "prepare" and a.benchmark == "mbppplus":
        raw = Path(a.raw_dir) / "mbppplus.jsonl"
        if not raw.exists():
            sys.exit(f"{raw} missing: run `download --benchmark mbppplus` first")
        n = dataset.build_mbpp_problem_file(raw, run / "problems.jsonl")
        print(f"{n} MBPP+ problems (seed {config.MBPP_SEED}) -> {run / 'problems.jsonl'}")
        return 0
    if a.command == "prepare":
        raws = sorted(Path(a.raw_dir).glob("test*.jsonl"))
        if not raws:
            sys.exit(f"no raw files in {a.raw_dir}: run `download` first")
        n = dataset.build_problem_file(raws, run / "problems.jsonl")
        print(f"{n} problems (contest_date >= {config.SINCE}) -> {run / 'problems.jsonl'}")
        return 0

    probs = _problems(run, a.fake)
    if a.limit:
        probs = probs[: a.limit]
    min_p = 1 if a.fake else a.min_problems

    def run_gate(stage):
        if stage == "env":
            g = verify.gate_env(run, cfgs)
        elif stage == "data":
            g = verify.gate_data(run, probs, min_p if not a.limit else 1,
                                 mbpp_raw=Path(a.raw_dir) / "mbppplus.jsonl")
        elif stage == "exec":
            g = verify.gate_exec(run)
        elif stage == "backend":
            g = verify.gate_backend(run, probs, cfgs, **({"backend_factory": factory} if factory else {}))
        else:
            g = verify.gate_post(run, probs, cfgs, **({"backend_factory": factory} if factory else {}))
        print(f"[verify {stage}] {g.status}")
        for c in g.checks:
            if c["status"] != "PASS":
                print(f"  {c['status']}: {c['name']} -- {c['evidence']}")
        return g.status

    if a.command == "verify":
        if not a.stage:
            sys.exit("--stage is required")
        return 1 if run_gate(a.stage) == "FAIL" else 0
    if a.command == "generate":
        kw = {"backend_factory": factory} if factory else {}
        print(generate.generate(run, probs, cfgs, limit=a.limit, **kw))
        return 0
    if a.command == "evaluate":
        names = [c.name for c in cfgs] if a.cfg else None
        print(f"{evaluate.evaluate(run, probs, names)} new exec rows")
        return 0
    if a.command == "report":
        print(report.report(run, out))
        return 0

    # all: gates before and after each stage; stop on FAIL
    stages = ["data", "exec"] + ([] if a.fake else ["env", "backend"])
    for s in stages:
        if run_gate(s) == "FAIL":
            print(f"stopped: gate {s} FAILED; see {run / 'VERIFICATION_REPORT.md'}")
            return 1
    kw = {"backend_factory": factory} if factory else {}
    generate.generate(run, probs, cfgs, limit=a.limit, **kw)
    evaluate.evaluate(run, probs)
    if run_gate("post") == "FAIL":
        print(f"stopped: gate post FAILED; see {run / 'VERIFICATION_REPORT.md'}")
        return 1
    print(report.report(run, out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
