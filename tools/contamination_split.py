"""Contamination sub-analysis (design section 5): LiveCodeBench accuracy before vs on/after 2025-03-01.

python -I contamination_split.py D:\\slm\\seminar\\runs\\main  > contamination_split.md
S0 (first sample) for every config, plus S1 (pass@k) for the multi-sample SLMs. Wilson 95% intervals.
"""
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

RUN = Path(sys.argv[1])
CUT = "2025-03-01"


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)


probs = {json.loads(l)["id"]: json.loads(l) for l in (RUN / "problems.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
late = {pid for pid, p in probs.items() if p["contest_date"][:10] >= CUT}
ex = [json.loads(l) for l in (RUN / "exec.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
by = defaultdict(lambda: defaultdict(list))
for e in ex:
    by[e["cfg"]][e["problem_id"]].append(e)

early_n, late_n = len(probs) - len(late), len(late)
mix = {d: (sum(1 for p in probs.values() if p["difficulty"] == d and p["id"] not in late),
           sum(1 for p in probs.values() if p["difficulty"] == d and p["id"] in late)) for d in ("easy", "medium", "hard")}

print(f"# Contamination split, LiveCodeBench ({RUN})\n")
print(f"Problems before {CUT}: {early_n}; on/after {CUT}: {late_n}. Difficulty mix (before / after): "
      + ", ".join(f"{d} {a}/{b}" for d, (a, b) in mix.items()) + "\n")
print(f"| config | S0 before {CUT} | S0 on/after {CUT} | difference (pp) | S1 before | S1 on/after |")
print("|---|---|---|---|---|---|")
for cfg in sorted(by):
    rows = by[cfg]
    def acc(pids, oracle):
        ok = 0
        n = 0
        for pid in pids:
            r = rows.get(pid)
            if not r:
                continue
            n += 1
            ok += any(x["hidden_pass"] for x in r) if oracle else min(r, key=lambda x: x["sample_idx"])["hidden_pass"]
        lo, hi = wilson(ok, n)
        return ok, n, f"{100 * ok / n:.1f}% [{100 * lo:.0f}, {100 * hi:.0f}] ({ok}/{n})" if n else "-"
    e0, ne, es = acc([p for p in probs if p not in late], False)
    l0, nl, ls = acc([p for p in probs if p in late], False)
    multi = max(len(r) for r in rows.values()) > 1
    e1 = acc([p for p in probs if p not in late], True)[2] if multi else "= S0"
    l1 = acc([p for p in probs if p in late], True)[2] if multi else "= S0"
    d = 100 * (l0 / nl - e0 / ne) if ne and nl else float("nan")
    print(f"| {cfg} | {es} | {ls} | {d:+.1f} | {e1} | {l1} |")
print("\nA drop after the cut-off for a model trained after it would hint at memorisation of the earlier problems; "
      "the difficulty mix differs between the two periods, so compare models within a column rather than absolute values.")
