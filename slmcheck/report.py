"""Turn a run directory into the results bundle: tables, figures, RESULTS.md, metadata, raw data."""
from __future__ import annotations

import csv
import json
import platform
import shutil
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path
from statistics import mean

from . import config
from .cascade import cascade_curve
from .evaluate import _load
from .generate import load_all
from .select import DIFFICULTIES, STRATEGIES, by_problem, per_config_table, select
from .stats import bootstrap_mean_ci, exact_mcnemar, gap_recovered, holm, wilson

REALISTIC = ["S2", "S3", "S4", "S5"]
FAIL_KINDS = ["wrong_answer", "timeout", "runtime_error", "empty"]


def _write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = list(dict.fromkeys(k for r in rows for k in r)) or ["empty"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()})


def _tiers(exec_rows):
    tiers = {}
    for r in exec_rows:
        tiers[r["cfg"]] = r.get("tier", "slm")
    slms = [c for c, t in tiers.items() if t == "slm"]
    llms = [c for c, t in tiers.items() if t == "llm"]
    return slms, llms


def _paired(rows_a: dict, rows_b: dict, strat_a: str, strat_b: str, tau=config.PRIMARY_TAU):
    pids = sorted(set(rows_a) & set(rows_b))
    a = [select(rows_a[p], strat_a, tau).correct for p in pids]
    b = [select(rows_b[p], strat_b, tau).correct for p in pids]
    only_a = sum(x and not y for x, y in zip(a, b))
    only_b = sum(y and not x for x, y in zip(a, b))
    diffs = [int(x) - int(y) for x, y in zip(a, b)]
    lo, hi = bootstrap_mean_ci(diffs, resamples=2000)
    return {"n": len(pids), "acc_a": sum(a) / max(1, len(a)), "acc_b": sum(b) / max(1, len(b)),
            "only_a": only_a, "only_b": only_b, "p": exact_mcnemar(only_a, only_b),
            "diff": mean(diffs) if diffs else 0.0, "diff_ci_lo": lo, "diff_ci_hi": hi}


def build_tables(exec_rows: list[dict], samples: list[dict]) -> dict[str, list[dict]]:
    slms, llms = _tiers(exec_rows)
    acc_rows = []
    for cfg in slms:
        acc_rows += per_config_table(exec_rows, cfg)
        for tau in config.TAUS:
            if tau != config.PRIMARY_TAU:
                acc_rows += [r for r in per_config_table(exec_rows, cfg, tau) if r["strategy"] == "S3"]
    for cfg in llms:
        acc_rows += [r for r in per_config_table(exec_rows, cfg) if r["strategy"] == "S0"]
    for r in acc_rows:
        lo, hi = wilson(round(r["accuracy"] * r["n"]), r["n"])
        r["acc_ci_lo"], r["acc_ci_hi"] = lo, hi
    look = {(r["cfg"], r["strategy"], r["tau"], r["difficulty"]): r for r in acc_rows}

    gap = []
    for slm in slms:
        for llm in llms:
            for d in DIFFICULTIES:
                s0 = look.get((slm, "S0", None, d))
                lr = look.get((llm, "S0", None, d))
                if not s0 or not lr:
                    continue
                for s in ["S1"] + REALISTIC:
                    r = look.get((slm, s, config.PRIMARY_TAU if s == "S3" else None, d))
                    gap.append({"slm": slm, "llm": llm, "difficulty": d, "strategy": s,
                                "acc_s0": s0["accuracy"], "acc_strategy": r["accuracy"],
                                "acc_llm": lr["accuracy"],
                                "gap_recovered": gap_recovered(r["accuracy"], s0["accuracy"],
                                                               lr["accuracy"])})

    false_pass = [{k: r[k] for k in ("cfg", "strategy", "tau", "difficulty", "n", "accept_rate",
                                     "false_pass_rate", "accuracy")}
                  for r in acc_rows if r["strategy"] in REALISTIC]

    silent = []
    for slm in slms:
        rows = by_problem(exec_rows, slm)
        for s in REALISTIC:
            picks = [select(r, s) for r in rows.values()]
            wrong = [p for p in picks if p.accepted and not p.correct]
            row = {"cfg": slm, "strategy": s, "accepted": sum(1 for p in picks if p.accepted),
                   "silent_bugs": len(wrong)}
            for k in FAIL_KINDS:
                row[k] = sum(1 for p in wrong if p.fail_kind == k)
            silent.append(row)

    casc = []
    for slm in slms:
        srows = [r for r in exec_rows if r["cfg"] == slm]
        for llm in llms:
            lrows = [r for r in exec_rows if r["cfg"] == llm]
            for s in REALISTIC:
                pts = cascade_curve(srows, lrows, s)
                casc += pts if s == "S2" else [p for p in pts if p["strategy"] == s]

    tests = []
    for slm in slms:
        rows = by_problem(exec_rows, slm)
        for s in ["S1"] + REALISTIC:
            tests.append({"comparison": f"{slm}:{s} vs {slm}:S0", **_paired(rows, rows, s, "S0")})
        for llm in llms:
            lrows = by_problem(exec_rows, llm)
            for s in ["S0"] + REALISTIC:
                tests.append({"comparison": f"{slm}:{s} vs {llm}:S0", **_paired(rows, lrows, s, "S0")})
    for t, ph in zip(tests, holm([t["p"] for t in tests])):
        t["p_holm"] = ph

    by_cfg = defaultdict(list)
    for s in samples:
        by_cfg[s["cfg"]].append(s)
    cost = []
    for cfg, ss in by_cfg.items():
        per_problem = defaultdict(float)
        for s in ss:
            per_problem[s["problem_id"]] += s.get("wall_s", 0.0)
        cost.append({"cfg": cfg, "samples": len(ss),
                     "mean_wall_s_per_sample": mean(s.get("wall_s", 0.0) for s in ss),
                     "mean_wall_s_per_problem_all_k": mean(per_problem.values()),
                     "mean_completion_tokens": mean(s.get("completion_tokens", 0) for s in ss),
                     "mean_thinking_chars": mean(s.get("thinking_chars", 0) for s in ss),
                     "errors": sum(1 for s in ss if s.get("error")),
                     "empty_code": sum(1 for s in ss if not s.get("code", "").strip())})
    return {"accuracy_by_strategy": acc_rows, "gap_recovered": gap, "false_pass": false_pass,
            "silent_bugs": silent,
            "cascade": casc, "mcnemar": tests, "cost": cost}


def _figures(tables: dict, out: Path) -> list[str]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    out.mkdir(parents=True, exist_ok=True)
    acc = [r for r in tables["accuracy_by_strategy"] if r["difficulty"] == "all"]
    slms = sorted({r["cfg"] for r in acc if r["accept_rate"] is not None or r["strategy"] != "S0"})
    llm_acc = {r["cfg"]: r["accuracy"] for r in acc
               if r["strategy"] == "S0" and r["cfg"] not in slms}
    files = []

    fig, ax = plt.subplots(figsize=(7, 3.2))
    strategies = ["S0", "S2", "S3", "S4", "S5", "S1"]
    w = 0.8 / len(strategies)
    for j, s in enumerate(strategies):
        vals = [next((r["accuracy"] for r in acc if r["cfg"] == c and r["strategy"] == s
                      and r["tau"] in (None, config.PRIMARY_TAU)), 0) for c in slms]
        ax.bar([i + j * w for i in range(len(slms))], vals, w, label=s)
    for name, v in llm_acc.items():
        ax.axhline(v, ls="--", lw=1, color="k")
        ax.text(len(slms) - 0.4, v, name, fontsize=7, va="bottom", ha="right")
    ax.set_xticks([i + 0.4 - w / 2 for i in range(len(slms))], slms, rotation=15, fontsize=7)
    ax.set_ylabel("accuracy (hidden tests)")
    ax.legend(fontsize=7, ncol=6)
    fig.tight_layout()
    fig.savefig(out / "fig_accuracy_by_strategy.png", dpi=200)
    plt.close(fig)
    files.append("fig_accuracy_by_strategy.png")

    fp = [r for r in tables["false_pass"] if r["difficulty"] == "all"
          and r["tau"] in (None, config.PRIMARY_TAU)]
    fig, ax = plt.subplots(figsize=(7, 3))
    for j, s in enumerate(REALISTIC):
        vals = [next((r["false_pass_rate"] or 0 for r in fp if r["cfg"] == c and r["strategy"] == s), 0)
                for c in slms]
        ax.bar([i + j * 0.2 for i in range(len(slms))], vals, 0.2, label=s)
    ax.set_xticks([i + 0.3 for i in range(len(slms))], slms, rotation=15, fontsize=7)
    ax.set_ylabel("false-pass rate")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(out / "fig_false_pass.png", dpi=200)
    plt.close(fig)
    files.append("fig_false_pass.png")

    casc = tables["cascade"]
    for llm in sorted({r["llm"] for r in casc}):
        fig, ax = plt.subplots(figsize=(5, 3.6))
        for slm in slms:
            pts = sorted((r for r in casc if r["llm"] == llm and r["slm"] == slm
                          and r["strategy"] in REALISTIC), key=lambda r: r["escalation_rate"])
            ends = [r for r in casc if r["llm"] == llm and r["slm"] == slm
                    and r["strategy"] in ("all-local", "all-cloud")]
            line = sorted(ends + pts, key=lambda r: r["escalation_rate"])
            ax.plot([r["escalation_rate"] for r in line], [r["accuracy"] for r in line],
                    marker="o", ms=3, label=slm)
        ax.set_xlabel("share of problems sent to the cloud LLM")
        ax.set_ylabel("accuracy")
        ax.set_title(f"local-first escalation to {llm}", fontsize=9)
        ax.legend(fontsize=6)
        fig.tight_layout()
        name = f"fig_cascade_{llm}.png"
        fig.savefig(out / name, dpi=200)
        plt.close(fig)
        files.append(name)
    return files


def _git_commit() -> str | None:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                              cwd=Path(__file__).parent, timeout=10).stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def report(run_dir: Path | str, out_dir: Path | str = "bundle") -> Path:
    run, out = Path(run_dir), Path(out_dir)
    exec_rows, samples = _load(run / "exec.jsonl"), load_all(run, "samples")
    if not exec_rows:
        raise SystemExit(f"no exec.jsonl rows in {run}; run `evaluate` first")
    fake = any(s.get("model_digest") == "fake" for s in samples)
    tables = build_tables(exec_rows, samples)
    for name, rows in tables.items():
        _write_csv(out / "tables" / f"{name}.csv", rows)
    figs = _figures(tables, out / "figures")
    raw = out / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    names = ["problems.jsonl", "exec.jsonl", "progress.log", "VERIFICATION_REPORT.md",
             "verify_state.json"] + [p.name for p in run.glob("s*__*.jsonl")]
    for f in names:
        if (run / f).exists():
            shutil.copy2(run / f, raw / f)
    if (run / "VERIFICATION_REPORT.md").exists():
        shutil.copy2(run / "VERIFICATION_REPORT.md", out / "VERIFICATION_REPORT.md")
    meta = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"), "fake": fake,
        "python": sys.version.split()[0], "platform": platform.platform(),
        "git_commit": _git_commit(), "since": config.SINCE,
        "n_problems": len({r["problem_id"] for r in exec_rows}),
        "configs": {c: {"samples": sum(1 for s in samples if s["cfg"] == c),
                        "digests": sorted({str(s.get("model_digest")) for s in samples if s["cfg"] == c})}
                    for c in sorted({s["cfg"] for s in samples})},
    }
    (out / "run_metadata.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    (out / "RESULTS.md").write_text(_results_md(tables, figs, meta), encoding="utf-8")
    return out


def _fmt(v):
    return "–" if v is None else (f"{v:.3f}" if isinstance(v, float) else str(v))


def _results_md(tables: dict, figs: list[str], meta: dict) -> str:
    lines = []
    if meta["fake"]:
        lines += ["# FAKE — NOT RESULTS", "", "Produced by the fake backend for pipeline testing only.", ""]
    lines += ["# Results summary", "",
              f"Problems: {meta['n_problems']} (contest_date >= {meta['since']}). "
              f"Generated {meta['generated_at']} on {meta['platform']}.", "",
              "## Accuracy by strategy, all difficulties (tables/accuracy_by_strategy.csv)", "",
              "| cfg | strategy | tau | accuracy | 95% CI | accept rate | false-pass rate |",
              "|---|---|---|---|---|---|---|"]
    for r in tables["accuracy_by_strategy"]:
        if r["difficulty"] == "all":
            lines.append(f"| {r['cfg']} | {r['strategy']} | {_fmt(r['tau'])} | {_fmt(r['accuracy'])} | "
                         f"[{_fmt(r['acc_ci_lo'])}, {_fmt(r['acc_ci_hi'])}] | {_fmt(r['accept_rate'])} | "
                         f"{_fmt(r['false_pass_rate'])} |")
    lines += ["", "## Gap recovered, all difficulties (tables/gap_recovered.csv)", "",
              "| slm | llm | strategy | gap recovered |", "|---|---|---|---|"]
    for r in tables["gap_recovered"]:
        if r["difficulty"] == "all":
            lines.append(f"| {r['slm']} | {r['llm']} | {r['strategy']} | {_fmt(r['gap_recovered'])} |")
    lines += ["", "## Silent bugs by type: accepted by the check but wrong (tables/silent_bugs.csv)", "",
              "| cfg | strategy | accepted | silent bugs | wrong answer | timeout | runtime error |",
              "|---|---|---|---|---|---|---|"]
    for r in tables["silent_bugs"]:
        lines.append(f"| {r['cfg']} | {r['strategy']} | {r['accepted']} | {r['silent_bugs']} | "
                     f"{r['wrong_answer']} | {r['timeout']} | {r['runtime_error']} |")
    lines += ["", "## Local-first escalation (tables/cascade.csv)", "",
              "| slm | llm | strategy | tau | escalated | accuracy | random | oracle |",
              "|---|---|---|---|---|---|---|---|"]
    for r in tables["cascade"]:
        lines.append(f"| {r['slm']} | {r['llm']} | {r['strategy']} | {_fmt(r['tau'])} | "
                     f"{_fmt(r['escalation_rate'])} | {_fmt(r['accuracy'])} | {_fmt(r['random_acc'])} | "
                     f"{_fmt(r['oracle_acc'])} |")
    lines += ["", "## Significance (tables/mcnemar.csv, Holm-adjusted)", "",
              "| comparison | acc A | acc B | p (Holm) |", "|---|---|---|---|"]
    for r in tables["mcnemar"]:
        lines.append(f"| {r['comparison']} | {_fmt(r['acc_a'])} | {_fmt(r['acc_b'])} | {_fmt(r['p_holm'])} |")
    lines += ["", "## Cost (tables/cost.csv)", "", "| cfg | samples | s/problem (all k) | tokens/sample | errors | empty |",
              "|---|---|---|---|---|---|"]
    for r in tables["cost"]:
        lines.append(f"| {r['cfg']} | {r['samples']} | {_fmt(r['mean_wall_s_per_problem_all_k'])} | "
                     f"{_fmt(r['mean_completion_tokens'])} | {r['errors']} | {r['empty_code']} |")
    lines += ["", "## Figures", ""] + [f"- figures/{f}" for f in figs] + [""]
    return "\n".join(lines)
