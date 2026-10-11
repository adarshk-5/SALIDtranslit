"""
analysis.py -- conjunct statistics and figures for the SALIDtranslit paper.

Run from the folder where evaluate.py wrote its outputs:
    python analysis.py

Inputs
  all_scores_summary.csv  (from evaluate.py)           -> Figure 1
  all.csv  (the verified dataset)                       -> Tables A/B, Figures 2-3
  ben_dev_eval.csv (from evaluate.py, optional)         -> Aksharamukha error rate per author

Outputs (in ./figures): PDF + PNG for each figure, and CSVs for each table.
"""

import os
import unicodedata
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
ALL_CSV = "/Users/adarshk/Downloads/NCSA SPIN/SALIDtranslit/data/all.csv"
SUMMARY_CSV = "all_scores_summary.csv"
BEN_DEV_EVAL_CSV = "ben_dev_eval.csv"
OUT_DIR = "figures"

VIRAMA_DEV, VIRAMA_BEN = "\u094D", "\u09CD"
DEV_BA, DEV_VA, BEN_BA = "\u092C", "\u0935", "\u09AC"
MIN_AUTHOR_N = 200                 # authors with fewer sentences are pooled in Figure 3

plt.rcParams.update({
    "font.size": 8, "axes.titlesize": 9, "axes.labelsize": 8,
    "legend.fontsize": 7, "xtick.labelsize": 7, "ytick.labelsize": 7,
    "axes.spines.top": False, "axes.spines.right": False,
})
# Distinct in greyscale too (hatches), since reviewers may print in B/W.
STYLE = {
    "aksharamukha":           ("Aksharamukha (default)", "#999999", ""),
    "aksharamukha_naive_va":  ("Naive all-va",           "#d95f02", "//"),
    "aksharamukha_conjunct_regex": ("Aksharamukha + conjunct regex", "#66a6d6", "xx"),
    "aksharamukha_bava_mode": ("Aksharamukha ba/va mode", "#7570b3", "\\\\"),
    "salidtranslit":          ("SALIDtranslit",          "#1b9e77", ""),
}


def save(fig, name):
    os.makedirs(OUT_DIR, exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(f"{OUT_DIR}/{name}.{ext}", dpi=200, bbox_inches="tight")
    plt.close(fig)


def nfc(s):
    return unicodedata.normalize("NFC", str(s)).strip()


# ---------------------------------------------------------------------------
# Figure 1: aggregate metrics look saturated; va recall exposes the failure
# ---------------------------------------------------------------------------
def fig_headline(summary_path=SUMMARY_CSV):
    df = pd.read_csv(summary_path)
    d = df[df.direction == "ben_dev"].set_index("system")
    metrics = [("chrf", "chrF", 1), ("exact_match", "Sentence\nexact match", 1),
               ("va_precision", "va\nprecision", 100), ("va_recall", "va\nrecall", 100)]
    systems = [s for s in STYLE if s in d.index]
    width = 0.8 / len(systems)

    fig, ax = plt.subplots(figsize=(6.3, 2.6))
    for k, s in enumerate(systems):
        label, color, hatch = STYLE[s]
        vals = [d.loc[s, m] * scale for m, _, scale in metrics]
        xs = [i + (k - (len(systems) - 1) / 2) * width for i in range(len(metrics))]
        bars = ax.bar(xs, vals, width, label=label, color=color, hatch=hatch,
                      edgecolor="black", linewidth=0.5)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 1.5, f"{v:.1f}", ha="center", va="bottom", rotation=90, fontsize=6)
    ax.set_xticks(range(len(metrics)))
    ax.set_xticklabels([lbl for _, lbl, _ in metrics])
    ax.set_ylabel("Score (%)")
    ax.set_ylim(0, 120)
    ax.set_title("Bengali \u2192 Devanagari: aggregate metrics vs. the va decision itself")
    ax.legend(loc="upper center", ncol=len(systems), frameon=False, bbox_to_anchor=(0.5, -0.22))
    save(fig, "fig1_headline")


# ---------------------------------------------------------------------------
# Table A / Figure 2: where do ba and va occur?
# ---------------------------------------------------------------------------
def load_all(path=ALL_CSV):
    base = pd.read_csv(path)
    base.columns = ["author", "title", "author_title", "bengali", "hindi"]
    return base


POSITIONS = ("conjunct-final", "isolated")


def collect_decisions(bengali_col, ref_col):
    """
    One record per ba/va decision: (position, first_member, reference_choice).

    The i-th ব of a Bengali sentence is paired with the i-th ब/व of the reference
    (the mapping is monotone); sentences where the counts differ are returned in
    `unpaired`.

      position     conjunct-final  : ব directly after a virama (্), e.g. স্ব
                   isolated        : every other position
      first_member the consonant before the virama (conjunct-final only)
    """
    records, unpaired = [], []
    for idx, (b, d) in enumerate(zip(bengali_col, ref_col)):
        b, d = nfc(b), nfc(d)
        found = []
        for i, ch in enumerate(b):
            if ch != BEN_BA:
                continue
            prev = b[i - 1] if i > 0 else ""
            if prev == VIRAMA_BEN:
                found.append(("conjunct-final", b[i - 2] if i > 1 else ""))
            else:
                found.append(("isolated", ""))
        chars = [ch for ch in d if ch in (DEV_BA, DEV_VA)]
        if len(found) != len(chars):
            unpaired.append(idx)
            continue
        for (pos, first), ch in zip(found, chars):
            records.append((pos, first, "va" if ch == DEV_VA else "ba"))
    return records, unpaired


def table_and_fig_positions(base):
    records, unpaired = collect_decisions(base["bengali"], base["hindi"])
    c = Counter((pos, ref) for pos, _, ref in records)
    total = sum(c.values())
    rows = [{"bengali_position": p, "reference": r, "count": c[(p, r)], "percent": 100 * c[(p, r)] / total}
            for p in POSITIONS for r in ("va", "ba")]
    table = pd.DataFrame(rows)
    os.makedirs(OUT_DIR, exist_ok=True)
    table.to_csv(f"{OUT_DIR}/table_a_positions.csv", index=False)
    print("\nTable A: ba/va decisions by position in the Bengali source")
    print(table.to_string(index=False, float_format=lambda x: f"{x:.3f}"))

    n_conj = c[("conjunct-final", "va")] + c[("conjunct-final", "ba")]
    print(f"\nAmong conjunct-final ব, {100 * c[('conjunct-final', 'va')] / n_conj:.1f}% are va in the reference "
          f"({c[('conjunct-final', 'ba')]:,} stay ba).")
    print("va outside conjunct-final position:",
          sum(c[(p, 'va')] for p in POSITIONS if p != "conjunct-final"))
    print(f"Sentences whose ব count differs from the reference ब/व count (unpaired): {len(unpaired)}")
    for i in unpaired[:10]:
        print(" ", base.loc[i, "author"], "|", base.loc[i, "title"]); print("  ", base.loc[i, "bengali"]); print("  ", base.loc[i, "hindi"])

    fig, ax = plt.subplots(figsize=(3.3, 1.9))
    labels = [f"{p}: {r}" for p in POSITIONS for r in ("va", "ba")]
    vals = [c[(p, r)] for p in POSITIONS for r in ("va", "ba")]
    colors = ["#1b9e77", "#bbbbbb"] * len(POSITIONS)
    ax.barh(range(len(vals)), [100 * v / total for v in vals], color=colors, edgecolor="black", linewidth=0.5)
    for i, v in enumerate(vals):
        ax.text(100 * v / total + 1, i, f"{v:,} ({100 * v / total:.2f}%)", va="center", fontsize=6)
    ax.set_yticks(range(len(vals)))
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.set_xlim(0, 135)
    ax.set_xlabel("% of ba/va decisions")
    ax.set_title("Position of ba/va in the Bengali source vs. reference")
    save(fig, "fig2_positions")
    return records


# ---------------------------------------------------------------------------
# Table C / Figure 4: is the va choice determined by the conjunct type?
# ---------------------------------------------------------------------------
ROMAN = {"ক": "k", "খ": "kh", "গ": "g", "ঘ": "gh", "ঙ": "ṅ", "চ": "c", "ছ": "ch", "জ": "j", "ঝ": "jh",
         "ঞ": "ñ", "ট": "ṭ", "ঠ": "ṭh", "ড": "ḍ", "ঢ": "ḍh", "ণ": "ṇ", "ত": "t", "থ": "th", "দ": "d",
         "ধ": "dh", "ন": "n", "প": "p", "ফ": "ph", "ব": "b", "ভ": "bh", "ম": "m", "য": "y", "র": "r",
         "ল": "l", "শ": "ś", "ষ": "ṣ", "স": "s", "হ": "h"}


def table_and_fig_conjunct_types(records, min_total=20):
    c = Counter((first, ref) for pos, first, ref in records if pos == "conjunct-final")
    firsts = sorted({f for f, _ in c}, key=lambda f: -(c[(f, "va")] + c[(f, "ba")]))
    rows = []
    for f in firsts:
        va, ba = c[(f, "va")], c[(f, "ba")]
        rows.append({"first_member": f, "roman": ROMAN.get(f, f), "n_va": va, "n_ba": ba,
                     "total": va + ba, "pct_va": 100 * va / (va + ba)})
    table = pd.DataFrame(rows)
    table.to_csv(f"{OUT_DIR}/table_c_conjunct_types.csv", index=False)
    print("\nTable C: reference choice by the consonant before the virama (conjunct-final only)")
    print(table.head(25).to_string(index=False, float_format=lambda x: f"{x:.1f}"))
    mixed = table[(table.total >= min_total) & (table.pct_va > 0) & (table.pct_va < 100)]
    print(f"\nConjunct types with >= {min_total} cases whose reference choice is MIXED (not determined by the type alone): {len(mixed)}")
    if len(mixed):
        print(mixed.to_string(index=False, float_format=lambda x: f"{x:.1f}"))
        print("A rule that only looks at the conjunct type cannot reproduce these; explain how SALID gets them right.")

    top = table.head(12).iloc[::-1]
    fig, ax = plt.subplots(figsize=(3.3, 0.25 * len(top) + 0.9))
    ax.barh(range(len(top)), top.pct_va, color="#1b9e77", edgecolor="black", linewidth=0.5, label="va")
    ax.barh(range(len(top)), 100 - top.pct_va, left=top.pct_va, color="#bbbbbb", edgecolor="black",
            linewidth=0.5, label="ba")
    ax.set_yticks(range(len(top)))
    ax.set_yticklabels([f"{r} + b  (n={int(n):,})" for r, n in zip(top.roman, top.total)])
    ax.set_xlim(0, 100)
    ax.set_xlabel("% of conjunct-final ba/va decisions")
    ax.set_title("Reference choice by first member of the conjunct")
    ax.legend(frameon=False, ncol=2, loc="upper center", bbox_to_anchor=(0.5, -0.28))
    save(fig, "fig4_conjunct_types")


# ---------------------------------------------------------------------------
# Table B / Figure 3: how widespread is the problem, per author?
# ---------------------------------------------------------------------------
def table_and_fig_authors(base, ben_dev_eval_path=BEN_DEV_EVAL_CSV):
    base = base.copy()
    base["has_va"] = base["hindi"].map(lambda s: DEV_VA in nfc(s))

    if os.path.exists(ben_dev_eval_path):
        ev = pd.read_csv(ben_dev_eval_path)
        if len(ev) == len(base):  # evaluate.py preserves row order
            base["akshar_wrong"] = [nfc(e) != nfc(a) for e, a in zip(ev["eval_output"], ev["aksharamukha_output"])]
        else:
            print("ben_dev_eval.csv length differs from all.csv; skipping per-author Aksharamukha errors")

    sizes = base["author"].value_counts()
    base["author"] = base["author"].where(base["author"].map(sizes) >= MIN_AUTHOR_N, "Other authors")
    g = base.groupby("author")
    table = g.agg(sentences=("has_va", "size"), pct_with_va=("has_va", lambda x: 100 * x.mean()))
    if "akshar_wrong" in base:
        table["pct_aksharamukha_wrong"] = g["akshar_wrong"].mean() * 100
    table.loc["ALL"] = [len(base), 100 * base["has_va"].mean()] + (
        [100 * base["akshar_wrong"].mean()] if "akshar_wrong" in base else [])
    table = table.sort_values("sentences", ascending=False)
    table.to_csv(f"{OUT_DIR}/table_b_authors.csv")
    print("\nTable B: sentences containing a va, per author")
    print(table.round(2).to_string())

    plot = table.drop(index="ALL").sort_values("pct_with_va", ascending=True)
    fig, ax = plt.subplots(figsize=(3.3, 0.35 * len(plot) + 0.9))
    ax.barh(range(len(plot)), plot["pct_with_va"], color="#d95f02", edgecolor="black", linewidth=0.5)
    ax.set_yticks(range(len(plot)))
    ax.set_yticklabels([f"{a} (n={int(n):,})" for a, n in zip(plot.index, plot["sentences"])])
    for i, v in enumerate(plot["pct_with_va"]):
        ax.text(v + 0.3, i, f"{v:.1f}%", va="center", fontsize=6)
    ax.axvline(100 * base["has_va"].mean(), color="black", linestyle="--", linewidth=0.7,
               label=f"all sentences ({100 * base['has_va'].mean():.1f}%)")
    ax.legend(frameon=False, loc="lower right", fontsize=6)
    ax.set_xlim(0, plot["pct_with_va"].max() * 1.18)
    ax.set_xlabel("% of sentences containing a va")
    ax.set_title("Sentences affected by the ba/va issue")
    save(fig, "fig3_authors")


if __name__ == "__main__":
    fig_headline()
    base = load_all()
    records = table_and_fig_positions(base)
    table_and_fig_conjunct_types(records)
    table_and_fig_authors(base)
    print(f"\nFigures and tables written to ./{OUT_DIR}/")