"""Print the README headline table (markdown) from bundle/<bench>/tables/accuracy_by_strategy.csv.

python tools/results_table.py [bundle_dir=bundle]
Reads only the result tables; every number in the README table comes from here.
"""
import csv
import sys
from pathlib import Path

BUNDLE = Path(sys.argv[1] if len(sys.argv) > 1 else "bundle")
BENCHES = [("livecodebench", "LCB"), ("mbppplus", "MBPP+")]
ORDER = ["qwen2.5-coder-1.5b", "qwen2.5-coder-7b", "deepseek-coder-6.7b", "qwen3-4b-nothink",
         "qwen3-4b-think", "gpt-oss-120b", "deepseek-v3.1", "llama-3.3-70b"]


def load(bench):
    rows = {}
    with open(BUNDLE / bench / "tables" / "accuracy_by_strategy.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["difficulty"] != "all" or r["tau"] not in ("", "1.0"):
                continue
            rows[(r["cfg"], r["strategy"])] = r
    return rows


def pct(rows, cfg, strat, col="accuracy"):
    # the CSVs store 4-decimal proportions; snap back to the exact count first so that e.g. 96/182 = 0.5275
    # prints 52.7 and not 52.8 (false-pass rates are over the accepted count, not over n)
    r = rows.get((cfg, strat))
    if not r or r[col] == "":
        return "–"
    v, n = float(r[col]), int(r["n"])
    if col == "false_pass_rate":
        n = round(float(r["accept_rate"]) * n)
    if n:
        v = round(v * n) / n
    return f"{100 * v + 1e-9:.1f}"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    data = {b: load(b) for b, _ in BENCHES}
    cfgs = sorted({c for d in data.values() for c, _ in d}, key=lambda c: ORDER.index(c) if c in ORDER else 99)
    head = ["model"]
    for _, short in BENCHES:
        head += [f"{short} S0", f"{short} S1", f"{short} S2", f"{short} S5", f"{short} S5 false-pass"]
    print("| " + " | ".join(head) + " |")
    print("|" + "---|" * len(head))
    for c in cfgs:
        cells = [c]
        for b, _ in BENCHES:
            d = data[b]
            multi = (c, "S1") in d and c not in ("qwen3-4b-think",)
            cells += [pct(d, c, "S0"), pct(d, c, "S1") if multi else "–", pct(d, c, "S2") if multi else "–",
                      pct(d, c, "S5") if multi else "–", pct(d, c, "S5", "false_pass_rate")]
        print("| " + " | ".join(cells) + " |")


if __name__ == "__main__":
    main()
