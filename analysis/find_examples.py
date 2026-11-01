"""List short accepted-but-wrong picks (silent bugs) as candidates for the paper's worked examples.

For each candidate the hidden tests are re-run one by one with the experiment's executor so that
the first failing hidden test can be quoted. Read-only with respect to the run data.
    python analysis/find_examples.py mbpp S5 12
"""
from __future__ import annotations

import sys

from common import MULTI, load, select

sys.path.insert(0, str(__import__("common").REPO))
from slmcheck import config  # noqa: E402
from slmcheck.dataset import Test  # noqa: E402
from slmcheck.executor import run_tests  # noqa: E402


def tests_of(prob, key):
    raw = prob[key]
    raw = eval(raw) if isinstance(raw, str) else raw
    return [Test(t["input"], t.get("output", ""), t["testtype"]) for t in raw]


def main(bench="mbpp", strategy="S5", max_lines=12, only=None):
    _, problems, samples, by = load(bench)
    seen = 0
    for cfg in MULTI:
        for p, rows in sorted(by[cfg].items()):
            if only and p not in only:
                continue
            pk = select(rows, strategy)
            if not pk.accepted or pk.correct:
                continue
            code = samples[(cfg, p, pk.sample_idx)]["code"]
            if len([ln for ln in code.splitlines() if ln.strip()]) > max_lines:
                continue
            prob = problems[p]
            hidden = tests_of(prob, "private")
            timeout = config.TIMEOUT_HARD_S if prob["difficulty"] == "hard" else config.TIMEOUT_S
            res = [run_tests(code, [t], prob.get("func_name"), timeout)[0] for t in hidden[:40]]
            first = next((i for i, r in enumerate(res) if not r.passed), None)
            seen += 1
            print("=" * 100)
            print(f"{cfg} {p} sample {pk.sample_idx} kind={pk.fail_kind} diff={prob['difficulty']}")
            print("TASK:", prob["content"][:600])
            print("PUBLIC:", [t.input[:300] for t in tests_of(prob, "public")])
            print("CODE:\n" + code)
            print(f"hidden tests: {len(hidden)}, run {len(res)}, failed {sum(not r.passed for r in res)}")
            if first is not None:
                t = hidden[first]
                print(f"FIRST FAIL #{first} status={res[first].status}: in={t.input[:500]!r} "
                      f"expected={t.output[:200]!r} got={str(res[first].got)[:200]!r}")
    print("candidates:", seen)


if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0] if a else "mbpp", a[1] if len(a) > 1 else "S5", int(a[2]) if len(a) > 2 else 12,
         set(a[3].split(",")) if len(a) > 3 else None)
