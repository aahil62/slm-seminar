"""Print-friendly vector figures for the journal paper (grayscale-safe: gray levels + hatches + markers).

Reads bundle/<bench>/tables/*.csv and analysis/out/*.csv; writes analysis/figures/*.pdf.
    python analysis/figures.py
"""
from __future__ import annotations

import csv
from collections import defaultdict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from common import BENCH_DIR, FIG, LLMS, MULTI, OUT, REAL, SHORT, SLMS  # noqa: E402

plt.rcParams.update({
    "font.family": "serif", "font.size": 7.5, "axes.titlesize": 8, "axes.labelsize": 7.5,
    "legend.fontsize": 6.5, "xtick.labelsize": 6.5, "ytick.labelsize": 6.5,
    "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 0.6,
    "grid.color": "0.88", "grid.linewidth": 0.5, "hatch.linewidth": 0.5,
    "pdf.fonttype": 42, "savefig.bbox": "tight", "savefig.pad_inches": 0.02,
})
GRAYS = ["0.92", "0.75", "0.58", "0.42", "0.25", "0.08"]
HATCH = ["", "////", "", "....", "xxxx", ""]
MARK = {"S2": "o", "S3": "s", "S4": "^", "S5": "D"}
SLM_MARK = dict(zip(SLMS, ["v", "s", "^", "o", "D"]))
SLM_LS = dict(zip(SLMS, [(0, (1, 1)), (0, (4, 1.5)), (0, (2, 1, 1, 1)), "-", (0, (6, 2))]))
BNAME = {"lcb": "LiveCodeBench", "mbpp": "MBPP+"}
W1, W2 = 2.6, 5.15  # single-panel / full text width in inches (sn-jnl text width is 372 pt)


def rows(path):
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return [r for r in csv.DictReader(f) if any(r.values())]


def table(bench, name):
    return rows(BENCH_DIR[bench] / "tables" / f"{name}.csv")


def primary(r):
    return r["strategy"] != "S3" or r["tau"] in ("1.0", "1", "")


def llms_in(bench):
    have = {r["cfg"] for r in table(bench, "accuracy_by_strategy")}
    return [m for m in LLMS if m in have]


def save(fig, name):
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / f"{name}.pdf")
    import os
    if os.environ.get("PREVIEW_DIR"):
        fig.savefig(os.path.join(os.environ["PREVIEW_DIR"], f"{name}.png"), dpi=130)
    plt.close(fig)


# ------------------------------------------------------------------ 1. accuracy by strategy
def fig_accuracy():
    fig, axes = plt.subplots(1, 2, figsize=(W2, 1.8), sharey=False)
    strats = ["S0", "S1", "S2", "S3", "S4", "S5"]
    for ax, bench in zip(axes, ("lcb", "mbpp")):
        look = {(r["cfg"], r["strategy"]): float(r["accuracy"]) for r in table(bench, "accuracy_by_strategy")
                if r["difficulty"] == "all" and primary(r)}
        w = 0.13
        for j, s in enumerate(strats):
            xs = [i + (j - 2.5) * w for i in range(len(MULTI))]
            ax.bar(xs, [100 * look[(c, s)] for c in MULTI], w, color=GRAYS[j], hatch=HATCH[j],
                   edgecolor="0.15", linewidth=0.4, label=s)
        refs = []  # reference lines are identified in the legend (values in Table 3), not by in-plot text
        for k, llm in enumerate(llms_in(bench)):
            refs.append(ax.axhline(100 * look[(llm, "S0")], color="0.1", ls=["--", ":"][k], lw=0.9, label=SHORT[llm]))
        if ("qwen3-4b-think", "S0") in look:
            refs.append(ax.axhline(100 * look[("qwen3-4b-think", "S0")], color="0.45", ls="-.", lw=0.8,
                                   label="Q3-4B-T (k=1)"))
        ax.set_xticks(range(len(MULTI)), [SHORT[c] for c in MULTI])
        ax.set_ylim(0, 100 if bench == "mbpp" else 65)
        if bench == "lcb":
            ax.set_ylabel("Hidden-test accuracy (%)")
        ax.set_title(f"({'ab'[bench == 'mbpp']}) {BNAME[bench]}")
        ax.yaxis.grid(True); ax.set_axisbelow(True)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, ncol=9, loc="lower center", frameon=False, bbox_to_anchor=(0.5, -0.12),
               columnspacing=0.8, handlelength=1.8, fontsize=5.8)
    save(fig, "fig_accuracy")


# ------------------------------------------------------------------ 2. acceptance vs false pass
def fig_accept_fp():
    fig, axes = plt.subplots(1, 3, figsize=(W2, 1.9), gridspec_kw={"width_ratios": [1, 1, 0.95], "wspace": 0.38})
    for ax, bench in zip(axes[:2], ("lcb", "mbpp")):
        for r in table(bench, "accuracy_by_strategy"):
            if r["difficulty"] != "all" or r["strategy"] not in REAL or not primary(r) or r["cfg"] not in MULTI:
                continue
            x, y = 100 * float(r["accept_rate"]), 100 * float(r["false_pass_rate"])
            ax.scatter(x, y, marker=MARK[r["strategy"]], s=26, facecolor="white" if r["strategy"] in ("S2", "S4") else "0.25",
                       edgecolor="0.1", linewidth=0.7, zorder=3)
            ax.annotate(SHORT[r["cfg"]].replace("QC-", "").replace("DSC-", "DS").replace("Q3-4B", "Q3"),
                        (x, y), xytext=(3, 2), textcoords="offset points", fontsize=4.3, color="0.35")
        ax.set_xlabel("Acceptance rate (%)")
        if bench == "lcb":
            ax.set_ylabel("False-pass rate (%)")
        ax.set_title(f"({'ab'[bench == 'mbpp']}) {BNAME[bench]}")
        ax.grid(True); ax.set_axisbelow(True)
        ax.set_ylim(0, 90 if bench == "lcb" else 30)
    handles = [plt.Line2D([], [], marker=MARK[s], ls="", markersize=5, markerfacecolor="white" if s in ("S2", "S4") else "0.25",
                          markeredgecolor="0.1", label={"S2": "S2 examples", "S3": "S3 self-tests",
                                                         "S4": "S4 majority", "S5": "S5 examples+majority"}[s]) for s in REAL]
    ax = axes[2]  # (c) false-pass rate by tier, LiveCodeBench, four k=5 models pooled
    data = rows(OUT / "fp_by_tier_lcb.csv")
    for j, s in enumerate(REAL):
        vals = [100 * float(next(x for x in data if x["tier"] == t and x["strategy"] == s)["fp"] or 0)
                for t in ("easy", "medium", "hard")]
        ax.bar([i + (j - 1.5) * 0.2 for i in range(3)], vals, 0.2, color=GRAYS[j + 1], hatch=HATCH[j + 1],
               edgecolor="0.15", linewidth=0.4)
    ax.set_xticks(range(3), ["Easy", "Med.", "Hard"])
    ax.set_ylim(0, 100); ax.yaxis.grid(True); ax.set_axisbelow(True)
    ax.set_title("(c) LCB, by difficulty")
    handles += [plt.Rectangle((0, 0), 1, 1, facecolor=GRAYS[j + 1], hatch=HATCH[j + 1], edgecolor="0.15", linewidth=0.4,
                              label=f"{s} bar") for j, s in enumerate(REAL)]
    fig.legend(handles=handles, ncol=4, loc="lower center", bbox_to_anchor=(0.5, -0.32), frameon=False, fontsize=6)
    save(fig, "fig_accept_fp")


# ------------------------------------------------------------------ 3. false pass by tier
def fig_fp_tier():
    data = rows(OUT / "fp_by_tier_lcb.csv")
    fig, ax = plt.subplots(figsize=(W1 * 1.35, 1.95))
    tiers = ["easy", "medium", "hard"]
    w = 0.2
    for j, s in enumerate(REAL):
        vals, labels = [], []
        for t in tiers:
            r = next(x for x in data if x["tier"] == t and x["strategy"] == s)
            vals.append(100 * float(r["fp"]) if r["fp"] else 0)
            labels.append(f"{r['wrong']}/{r['accepted']}")
        xs = [i + (j - 1.5) * w for i in range(3)]
        bars = ax.bar(xs, vals, w, color=GRAYS[j + 1], hatch=HATCH[j + 1], edgecolor="0.15", linewidth=0.4, label=s)
        for b, lab in zip(bars, labels):
            ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 1.5, lab, ha="center", va="bottom",
                    fontsize=5, rotation=90, color="0.25")
    ax.set_xticks(range(3), ["Easy", "Medium", "Hard"])
    ax.set_ylabel("False-pass rate (%)"); ax.set_ylim(0, 125); ax.set_yticks(range(0, 101, 20))
    ax.yaxis.grid(True); ax.set_axisbelow(True)
    ax.legend(ncol=4, frameon=False, loc="upper left")
    save(fig, "fig_fp_tier")


# ------------------------------------------------------------------ 4. silent-bug types
def fig_silent():
    data = rows(OUT / "silent_types.csv")
    fig, ax = plt.subplots(figsize=(W2, 2.0))
    labels, y = [], 0
    kinds = [("wrong_answer", "Wrong answer", "0.35", ""), ("timeout", "Time limit", "0.8", "////"),
             ("runtime_error", "Runtime error", "white", "....")]
    for bench in ("lcb", "mbpp"):
        for s in REAL:
            r = next(x for x in data if x["bench"] == bench and x["group"] == "multi" and x["strategy"] == s)
            left = 0
            acc = int(r["accepted"] or 0)
            for k, name, col, h in kinds:
                v = int(r.get(k) or 0)
                share = 100 * v / acc if acc else 0
                ax.barh(y, share, left=left, color=col, hatch=h, edgecolor="0.15", linewidth=0.4,
                        label=name if y == 0 else None, height=0.7)
                left += share
            ax.text(left + 0.8, y, f"{r['silent']} of {acc} accepted", va="center", fontsize=6.5, color="0.25")
            labels.append(f"{BNAME[bench]} {s}")
            y += 1
        y += 0.5
    ticks = [0, 1, 2, 3, 4.5, 5.5, 6.5, 7.5]
    ax.set_yticks(ticks, labels); ax.invert_yaxis()
    ax.set_xlabel("Accepted picks that are wrong (%), by hidden-test failure type (four k=5 models pooled)")
    ax.set_xlim(0, 75); ax.xaxis.grid(True); ax.set_axisbelow(True)
    ax.legend(ncol=1, frameon=False, loc="upper right")
    save(fig, "fig_silent_types")


# ------------------------------------------------------------------ 5. escalation curves
def fig_cascade():
    benches = ("lcb", "mbpp")
    pairs = [(b, LLMS[0]) for b in benches]  # primary cloud model only; the second one is in the table
    nrow = 2 if len(pairs) > 2 else 1
    fig, axes = plt.subplots(nrow, len(pairs) // nrow, figsize=(W2, 1.9 * nrow), squeeze=False)
    order = sorted(pairs, key=lambda p: (LLMS.index(p[1]), benches.index(p[0])))
    for ax, (bench, llm) in zip(axes.flat, order):
        c = [r for r in table(bench, "cascade") if r["llm"] == llm]
        cloud = 100 * float(next(r["accuracy"] for r in c if r["strategy"] == "all-cloud"))
        ax.axhline(cloud, color="0.1", ls="--", lw=0.8)
        ax.text(1.0, cloud + 0.6, "all to cloud", fontsize=6.5, ha="right", va="bottom")
        for cfg in SLMS:
            mine = [r for r in c if r["slm"] == cfg]
            local = next(r for r in mine if r["strategy"] == "all-local")
            s3 = sorted([r for r in mine if r["strategy"] == "S3"], key=lambda r: float(r["tau"]))
            pts = [(0.0, cloud)] + [(1 - float(r["escalation_rate"]), 100 * float(r["accuracy"])) for r in s3] \
                + [(1.0, 100 * float(local["accuracy"]))]
            pts.sort()
            ax.plot([p[0] for p in pts], [p[1] for p in pts], color="0.55", lw=0.6, ls=SLM_LS[cfg])
            for s in ("S2", "S5"):
                r = next(x for x in mine if x["strategy"] == s)
                x, yv = 1 - float(r["escalation_rate"]), 100 * float(r["accuracy"])
                ax.scatter(x, yv, marker=SLM_MARK[cfg], s=24, zorder=3,
                           facecolor="0.15" if s == "S5" else "white", edgecolor="0.1", linewidth=0.7)
                ax.scatter(x, 100 * float(r["random_acc"]), marker="x", s=12, color="0.55", linewidth=0.6, zorder=2)
        ax.set_xlim(-0.03, 1.03)
        ax.set_xlabel("Share of problems answered locally")
        if ax is axes.flat[0] or nrow > 1 and ax is axes.flat[len(pairs) // nrow]:
            ax.set_ylabel("System accuracy (%)")
        ax.set_title(f"{BNAME[bench]} (cloud: {SHORT[llm]})", fontsize=7)
        ax.grid(True); ax.set_axisbelow(True)
    handles = [plt.Line2D([], [], marker=SLM_MARK[c], ls=SLM_LS[c], color="0.55", markerfacecolor="0.15",
                          markeredgecolor="0.1", markersize=4.5, lw=0.6, label=SHORT[c]) for c in SLMS]
    handles += [plt.Line2D([], [], marker="o", ls="", markerfacecolor="white", markeredgecolor="0.1", label="S2 trigger (hollow)"),
                plt.Line2D([], [], marker="o", ls="", markerfacecolor="0.15", markeredgecolor="0.1", label="S5 trigger (filled)"),
                plt.Line2D([], [], marker="x", ls="", color="0.55", label="random escalation, same rate")]
    fig.subplots_adjust(wspace=0.22)
    fig.legend(handles=handles, ncol=4, frameon=False, loc="lower center", bbox_to_anchor=(0.5, -0.24 if nrow == 1 else -0.07), fontsize=6)
    save(fig, "fig_cascade")


# ------------------------------------------------------------------ 6. cost
def fig_cost():
    cost = rows(OUT / "cost.csv")
    casc = rows(OUT / "cascade_cost.csv")
    fig, axes = plt.subplots(1, 2, figsize=(W2, 1.65), gridspec_kw={"width_ratios": [1.15, 1]})
    ax = axes[0]
    cfgs = SLMS + [m for m in LLMS if any(r["cfg"] == m for r in cost)]
    w = 0.38
    for j, bench in enumerate(("lcb", "mbpp")):
        vals = []
        for c in cfgs:
            r = next((x for x in cost if x["bench"] == bench and x["cfg"] == c), None)
            vals.append(float(r["tokens_per_solved"]) if r and r["tokens_per_solved"] else 0)
        ax.bar([i + (j - 0.5) * w for i in range(len(cfgs))], vals, w, color=["0.35", "0.85"][j],
               hatch=["", "////"][j], edgecolor="0.15", linewidth=0.4, label=BNAME[bench])
    ax.set_yscale("log")
    ax.set_xticks(range(len(cfgs)), [SHORT[c] for c in cfgs], rotation=30, ha="right")
    ax.set_ylabel("Output tokens per solved problem")
    ax.set_title("(a) Generation cost per solved problem")
    ax.yaxis.grid(True, which="both"); ax.set_axisbelow(True); ax.legend(frameon=False)
    ax = axes[1]
    llm = "gpt-oss-120b"
    for bench, face in (("lcb", "0.15"), ("mbpp", "white")):
        for cfg in SLMS:
            r = next((x for x in casc if x["bench"] == bench and x["llm"] == llm and x["slm"] == cfg
                      and x["strategy"] == "S5"), None)
            if r:
                ax.scatter(100 * float(r["cloud_token_share"]), 100 * float(r["accuracy"]), marker=SLM_MARK[cfg],
                           s=26, facecolor=face, edgecolor="0.1", linewidth=0.7, zorder=3)
        allc = next(x for x in cost if x["bench"] == bench and x["cfg"] == llm)
        ax.scatter(100, 100 * int(allc["solved"]) / (200 if bench == "mbpp" else 182), marker="*", s=60,
                   facecolor=face, edgecolor="0.1", linewidth=0.7, zorder=3)
    ax.set_xlabel("Cloud output tokens used (% of all-cloud)")
    ax.set_ylabel("Accuracy (%)")
    ax.set_title(f"(b) S5 escalation to {SHORT[llm]}")
    ax.set_xlim(0, 105); ax.grid(True); ax.set_axisbelow(True)
    handles = [plt.Line2D([], [], marker=SLM_MARK[c], ls="", markerfacecolor="0.6", markeredgecolor="0.1", label=SHORT[c]) for c in SLMS]
    handles += [plt.Line2D([], [], marker="*", ls="", markersize=8, markerfacecolor="0.6", markeredgecolor="0.1", label="cloud only"),
                plt.Line2D([], [], marker="o", ls="", markerfacecolor="0.15", markeredgecolor="0.1", label="filled: LCB"),
                plt.Line2D([], [], marker="o", ls="", markerfacecolor="white", markeredgecolor="0.1", label="hollow: MBPP+")]
    ax.legend(handles=handles, fontsize=6, frameon=False, loc="center right", ncol=1)
    save(fig, "fig_cost")


# ------------------------------------------------------------------ 7. contamination split
def fig_contam():
    data = rows(OUT / "contamination.csv")
    cfgs = [c for c in SLMS + LLMS if any(r["cfg"] == c for r in data)]
    fig, ax = plt.subplots(figsize=(W1 * 1.45, 2.3))
    for i, c in enumerate(cfgs):
        e = next(r for r in data if r["cfg"] == c and r["window"] == "early")
        l = next(r for r in data if r["cfg"] == c and r["window"] == "late")
        for key, mk, dy in (("acc_S0", "o", -0.12), ("acc_S0_std", "s", 0.12)):
            a, b = 100 * float(e[key]), 100 * float(l[key])
            ax.plot([a, b], [i + dy, i + dy], color="0.6", lw=0.8)
            ax.scatter(a, i + dy, marker=mk, s=20, facecolor="white", edgecolor="0.1", linewidth=0.7, zorder=3)
            ax.scatter(b, i + dy, marker=mk, s=20, facecolor="0.15", edgecolor="0.1", linewidth=0.7, zorder=3)
    ax.set_yticks(range(len(cfgs)), [SHORT[c] for c in cfgs]); ax.invert_yaxis()
    ax.set_xlabel("First-sample accuracy (%)")
    ax.xaxis.grid(True); ax.set_axisbelow(True)
    e0 = next(r for r in data if r["window"] == "early"); l0 = next(r for r in data if r["window"] == "late")
    handles = [plt.Line2D([], [], marker="o", ls="", markerfacecolor="white", markeredgecolor="0.1",
                          label=f"before 2025-03-01 (n={e0['n']})"),
               plt.Line2D([], [], marker="o", ls="", markerfacecolor="0.15", markeredgecolor="0.1",
                          label=f"2025-03-01 or later (n={l0['n']})"),
               plt.Line2D([], [], marker="o", ls="", color="0.5", label="circle: raw"),
               plt.Line2D([], [], marker="s", ls="", color="0.5", label="square: difficulty-standardised")]
    ax.legend(handles=handles, fontsize=6.3, frameon=False, ncol=2, loc="upper center", bbox_to_anchor=(0.45, -0.2))
    save(fig, "fig_contam")


if __name__ == "__main__":
    for f in (fig_accuracy, fig_accept_fp, fig_fp_tier, fig_silent, fig_cascade, fig_cost, fig_contam):
        f()
        print("wrote", f.__name__)
