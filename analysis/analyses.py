"""Extra analyses for the journal paper, computed offline from the saved run (bundle/<bench>/raw).

Writes CSVs to analysis/out/. Never touches run data. Re-run after the bundle is rebuilt:
    python analysis/analyses.py
"""
from __future__ import annotations

import random
from collections import Counter, defaultdict

from common import (LLMS, MULTI, REAL, SLMS, llm_ok, load, present_llms, select, write_csv)

LATE = "2025-03-01"
TIERS = ["easy", "medium", "hard"]
BOOT = 2000


def ttype(prob):
    pub = prob["public"]
    pub = eval(pub) if isinstance(pub, str) else pub
    return pub[0]["testtype"] if pub else "?"


def acc(by, cfg, pids, strategy="S0"):
    rows = by[cfg]
    ok = [select(rows[p], strategy).correct for p in pids if p in rows]
    return (sum(ok) / len(ok)) if ok else None, len(ok)


# ---------------------------------------------------------------- contamination (LiveCodeBench)
def contamination():
    _, problems, _, by = load("lcb")
    early = [p for p, d in problems.items() if d["contest_date"] < LATE]
    late = [p for p, d in problems.items() if d["contest_date"] >= LATE]
    mix_all = Counter(problems[p]["difficulty"] for p in problems)
    out = []
    for win, pids in (("early", early), ("late", late)):
        mix = Counter(problems[p]["difficulty"] for p in pids)
        dates = sorted(problems[p]["contest_date"] for p in pids)
        for cfg in SLMS + present_llms(by):
            row = {"window": win, "first_date": dates[0], "last_date": dates[-1], "n": len(pids),
                   "n_easy": mix["easy"], "n_medium": mix["medium"], "n_hard": mix["hard"], "cfg": cfg}
            for s in ("S0", "S1", "S5"):
                if cfg not in SLMS and s != "S0":
                    continue
                row[f"acc_{s}"], _ = acc(by, cfg, pids, s)
            # difficulty-standardised S0 accuracy: tier accuracies reweighted to the full-window mix
            std = 0.0
            for t in TIERS:
                tp = [p for p in pids if problems[p]["difficulty"] == t]
                a, _ = acc(by, cfg, tp)
                std += (a or 0.0) * mix_all[t] / len(problems)
            row["acc_S0_std"] = std
            out.append(row)
    write_csv("contamination.csv", out)


# ---------------------------------------------------------------- false passes by tier, pooled
def fp_by_tier():
    out = []
    _, problems, _, by = load("lcb")
    for t in TIERS + ["all"]:
        for s in REAL:
            acc_n = wrong = 0
            for cfg in MULTI:
                for p, rows in by[cfg].items():
                    if t != "all" and problems[p]["difficulty"] != t:
                        continue
                    pk = select(rows, s)
                    if pk.accepted:
                        acc_n += 1
                        wrong += not pk.correct
            out.append({"tier": t, "strategy": s, "accepted": acc_n, "wrong": wrong,
                        "fp": wrong / acc_n if acc_n else None})
    write_csv("fp_by_tier_lcb.csv", out)


# ---------------------------------------------------------------- silent-bug types
def silent_types():
    out = []
    for bench in ("lcb", "mbpp"):
        _, problems, samples, by = load(bench)
        for group, cfgs in (("multi", MULTI), ("think", ["qwen3-4b-think"])):
            for s in REAL:
                c = Counter()
                for cfg in cfgs:
                    for p, rows in by[cfg].items():
                        pk = select(rows, s)
                        if not pk.accepted:
                            continue
                        c["accepted"] += 1
                        if pk.correct:
                            continue
                        c["silent"] += 1
                        c[pk.fail_kind or "unknown"] += 1
                        c[f"tier_{problems[p]['difficulty']}"] += 1
                        tt = ttype(problems[p])
                        c[f"type_{tt}"] += 1
                        code = samples.get((cfg, p, pk.sample_idx), {}).get("code", "")
                        c["loc_sum"] += len([ln for ln in code.splitlines() if ln.strip()])
                out.append({"bench": bench, "group": group, "strategy": s, **c})
    write_csv("silent_types.csv", out)


# ---------------------------------------------------------------- token cost
def tokens(samples, cfg, pids=None):
    return sum(int(float(s.get("completion_tokens") or 0)) for (c, p, _), s in samples.items()
               if c == cfg and (pids is None or p in pids))


def cost():
    out, casc = [], []
    for bench in ("lcb", "mbpp"):
        _, problems, samples, by = load(bench)
        n = len(problems)
        for cfg in SLMS + present_llms(by):
            tok = tokens(samples, cfg)
            ptok = sum(int(float(s.get("prompt_tokens") or 0)) for (c, _, _), s in samples.items() if c == cfg)
            nsamp = sum(1 for (c, _, _) in samples if c == cfg)
            strat = "S5" if cfg in MULTI else "S0"
            a, _ = acc(by, cfg, list(problems), strat)
            solved = round(a * n)
            out.append({"bench": bench, "cfg": cfg, "samples": nsamp, "prompt_tokens": ptok,
                        "completion_tokens": tok, "tokens_per_problem": tok / n, "strategy": strat,
                        "solved": solved, "tokens_per_solved": tok / solved if solved else None})
        for llm in present_llms(by):
            ok = llm_ok(by, llm)
            per_p = defaultdict(int)
            for (c, p, _), s in samples.items():
                if c == llm:
                    per_p[p] += int(float(s.get("completion_tokens") or 0))
            total = sum(per_p.values())
            for cfg in SLMS:
                for s in REAL:
                    picks = {p: select(rows, s) for p, rows in by[cfg].items()}
                    esc = [p for p, pk in picks.items() if not pk.accepted]
                    final = [pk.correct if pk.accepted else ok[p] for p, pk in picks.items()]
                    casc.append({"bench": bench, "llm": llm, "slm": cfg, "strategy": s,
                                 "local_share": 1 - len(esc) / n, "accuracy": sum(final) / n,
                                 "cloud_tokens": sum(per_p[p] for p in esc),
                                 "cloud_token_share": sum(per_p[p] for p in esc) / total if total else None,
                                 "local_tokens": tokens(samples, cfg)})
    write_csv("cost.csv", out)
    write_csv("cascade_cost.csv", casc)


# ---------------------------------------------------------------- bootstrap CI for gap recovered
def gap_ci():
    out = []
    for bench in ("lcb", "mbpp"):
        _, problems, _, by = load(bench)
        pids = sorted(problems)
        for llm in present_llms(by):
            ok = llm_ok(by, llm)
            for cfg in MULTI:
                s0 = {p: select(by[cfg][p], "S0").correct for p in pids}
                for s in ["S1"] + REAL:
                    sx = {p: select(by[cfg][p], s).correct for p in pids}
                    rng, vals = random.Random(20261016), []
                    for _ in range(BOOT):
                        smp = [pids[rng.randrange(len(pids))] for _ in pids]
                        a0 = sum(s0[p] for p in smp); ax = sum(sx[p] for p in smp)
                        al = sum(ok[p] for p in smp)
                        if al - a0 > 0:
                            vals.append((ax - a0) / (al - a0))
                    vals.sort()
                    lo = vals[int(0.025 * len(vals))] if vals else None
                    hi = vals[int(0.975 * len(vals)) - 1] if vals else None
                    out.append({"bench": bench, "llm": llm, "slm": cfg, "strategy": s,
                                "ci_lo": lo, "ci_hi": hi, "valid_resamples": len(vals)})
    write_csv("gap_ci.csv", out)


# ---------------------------------------------------------------- complementarity with the cloud
def overlap():
    out = []
    for bench in ("lcb", "mbpp"):
        _, problems, _, by = load(bench)
        for llm in present_llms(by):
            ok = llm_ok(by, llm)
            for cfg in SLMS:
                for s in ("S0", "S1", "S5"):
                    loc = {p: select(by[cfg][p], s).correct for p in problems}
                    out.append({"bench": bench, "llm": llm, "slm": cfg, "strategy": s,
                                "both": sum(loc[p] and ok[p] for p in problems),
                                "local_only": sum(loc[p] and not ok[p] for p in problems),
                                "cloud_only": sum(ok[p] and not loc[p] for p in problems),
                                "neither": sum(not loc[p] and not ok[p] for p in problems)})
    write_csv("overlap.csv", out)


# ---------------------------------------------------------------- run facts for the text
def facts():
    out = []
    for bench in ("lcb", "mbpp"):
        exec_rows, problems, samples, by = load(bench)
        mix = Counter(p["difficulty"] for p in problems.values())
        out += [{"bench": bench, "key": f"n_{t}", "value": mix[t]} for t in TIERS]
        types = Counter(ttype(p) for p in problems.values())
        out += [{"bench": bench, "key": f"type_{t}", "value": v} for t, v in types.items()]
        dates = sorted(p["contest_date"] for p in problems.values())
        out += [{"bench": bench, "key": "first_date", "value": dates[0]},
                {"bench": bench, "key": "last_date", "value": dates[-1]},
                {"bench": bench, "key": "n_late", "value": sum(d >= LATE for d in dates)}]
        for cfg in SLMS + LLMS:
            ss = [s for (c, _, _), s in samples.items() if c == cfg]
            if not ss:
                continue
            cap = 8192 if cfg in ("qwen3-4b-think", "gpt-oss-120b") else 1024
            capped = [s for s in ss if int(float(s.get("completion_tokens") or 0)) >= cap]
            out.append({"bench": bench, "key": f"{cfg}_samples", "value": len(ss)})
            out.append({"bench": bench, "key": f"{cfg}_capped", "value": len(capped)})
            # capped replies split by what was cut: no code at all (prose only), code cut mid-block (odd number
            # of ``` fences), or a complete block followed by cut-off prose
            fences = [(s.get("raw_text") or "").count("```") for s in capped]
            out.append({"bench": bench, "key": f"{cfg}_cappednocode", "value": sum(f == 0 for f in fences)})
            out.append({"bench": bench, "key": f"{cfg}_cappedcodecut", "value": sum(f % 2 == 1 for f in fences)})
            out.append({"bench": bench, "key": f"{cfg}_cappedcomplete", "value": sum(f >= 2 and f % 2 == 0 for f in fences)})
            if cfg in LLMS:  # pass rate among answers that contain a complete code block
                hp = {(r["problem_id"], r["sample_idx"]): r["hidden_pass"] for r in exec_rows if r["cfg"] == cfg}
                comp = [s for s in ss if (s.get("raw_text") or "").count("```") >= 2
                        and (s.get("raw_text") or "").count("```") % 2 == 0
                        or (int(float(s.get("completion_tokens") or 0)) < cap and (s.get("code") or "").strip())]
                out.append({"bench": bench, "key": f"{cfg}_complete", "value": len(comp)})
                out.append({"bench": bench, "key": f"{cfg}_completepass",
                            "value": sum(bool(hp.get((s["problem_id"], int(s["sample_idx"])))) for s in comp)})
            out.append({"bench": bench, "key": f"{cfg}_prompt_tokens",
                        "value": sum(int(float(s.get("prompt_tokens") or 0)) for s in ss)})
            out.append({"bench": bench, "key": f"{cfg}_completion_tokens",
                        "value": sum(int(float(s.get("completion_tokens") or 0)) for s in ss)})
        # self-test usability: share of problems where at least one parsable self-test exists
        for cfg in SLMS:
            rows = by[cfg]
            usable = sum(1 for p, rs in rows.items() if any(r["self"] for r in rs))
            out.append({"bench": bench, "key": f"{cfg}_selftest_usable", "value": usable})
    write_csv("facts.csv", out)


# ---------------------------------------------------------------- results on the post-split window only
def late_split():
    """Cloud accuracy, local S0/S5 accuracy, gap recovered and S5 escalation restricted to problems dated
    on or after LATE. Needed for a cloud model released after the problem window (DeepSeek-V3.1)."""
    _, problems, _, by = load("lcb")
    late = sorted(p for p, d in problems.items() if d["contest_date"] >= LATE)
    out = []
    for llm in present_llms(by):
        ok = llm_ok(by, llm)
        acc_llm = sum(ok[p] for p in late) / len(late)
        for cfg in SLMS:
            s0 = [select(by[cfg][p], "S0").correct for p in late]
            picks = [select(by[cfg][p], "S5") for p in late]
            s5 = [pk.correct for pk in picks]
            final = [pk.correct if pk.accepted else ok[p] for pk, p in zip(picks, late)]
            a0, a5 = sum(s0) / len(late), sum(s5) / len(late)
            out.append({"llm": llm, "slm": cfg, "n": len(late), "acc_llm": acc_llm, "acc_S0": a0, "acc_S5": a5,
                        "gap_S5": (a5 - a0) / (acc_llm - a0) if acc_llm > a0 else None,
                        "local_share_S5": sum(pk.accepted for pk in picks) / len(late),
                        "casc_S5": sum(final) / len(late)})
    write_csv("late_split.csv", out)


if __name__ == "__main__":
    for f in (contamination, fp_by_tier, silent_types, cost, gap_ci, overlap, facts, late_split):
        f()
        print("done", f.__name__)
