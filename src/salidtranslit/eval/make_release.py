"""
make_release_sample.py -- draw the public, conjunct-stratified release from the full corpus.

Whole sentences are released. Each sampling stratum is the consonant immediately before
the sequence virama (U+09CD) + ব (U+09AC) together with the reference label (ba/va), plus
one control stratum of non-conjunct ব. For every stratum the script draws up to
--per-stratum sentences (up to --control for the control), without replacement.

How a sentence is chosen
  1. Eligibility: the author is permitted (--exclude-authors / --allow-authors), the sentence
     passes the optional length limits, its ব count matches its reference ब/व count, and it is
     not an exact duplicate (after NFC and whitespace normalisation) of an earlier row.
  2. Strata are processed from the rarest to the most common, the control last, so that
     rare strata get first pick. Sentences already chosen for an earlier stratum count
     toward every stratum they contain; only the shortfall is drawn.
  3. Within a stratum, --mode balanced (default) repeatedly takes a random sentence from the
     least-represented (author x sentence-length-bin) group; --mode random draws uniformly.
     Length bins are quantile bins of the eligible sentences' word counts.
  4. A sentence is released once, with ALL of its ব occurrences labelled.

Usage
    python make_release_sample.py --list-authors
    python make_release_sample.py --exclude-authors "Some Author" --seed 0
    python make_release_sample.py --per-stratum 200 --control 200 --length-bins 3

Outputs (in ./release)
    release_sentences.csv      one row per sentence (public id, author, title, Bengali, reference, ...)
    release_occurrences.csv    one row per labelled ব occurrence in those sentences
    sampling_report.csv        per-stratum frequencies in the corpus, eligible, drawn, released
    sampling_report_composition.csv   per-stratum author and length-bin composition
    manifest.json              parameters, seed, input checksum, filter counts, bin edges
    internal_row_map.csv       id -> row in the full corpus.  DO NOT RELEASE.
"""

import argparse
import hashlib
import json
import os
import random
import re
import sys
import unicodedata
from collections import Counter, defaultdict

import numpy as np
import pandas as pd

ALL_CSV = "/Users/adarshk/Downloads/NCSA SPIN/SALIDtranslit/data/all.csv"
COLUMNS = ["author", "title", "author_title", "bengali", "hindi"]
VIRAMA_BEN, BEN_BA = "\u09CD", "\u09AC"
DEV_BA, DEV_VA = "\u092C", "\u0935"
CONTROL = ("(non-conjunct)", "ba")


def nfc(s):
    return unicodedata.normalize("NFC", str(s))


def norm_key(s):
    return re.sub(r"\s+", " ", nfc(s)).strip()


def public_id(bengali):
    return hashlib.sha1(norm_key(bengali).encode("utf-8")).hexdigest()[:10]


def parse_occurrences(bengali, reference):
    """
    One record per ব in the Bengali sentence: token index, kind (conjunct = directly after a
    virama; isolated = anywhere else), preceding consonant (conjunct only) and the reference
    label. The i-th ব is paired with the i-th ब/व of the reference. Returns None if the counts
    differ, so the sentence cannot be labelled reliably.
    """
    found = []
    for ti, tok in enumerate(nfc(bengali).split()):
        for i, ch in enumerate(tok):
            if ch == BEN_BA:
                if i > 0 and tok[i - 1] == VIRAMA_BEN:
                    found.append((ti, "conjunct", tok[i - 2] if i > 1 else ""))
                else:
                    found.append((ti, "isolated", ""))
    labels = ["va" if c == DEV_VA else "ba" for c in nfc(reference) if c in (DEV_BA, DEV_VA)]
    if len(found) != len(labels):
        return None
    return [{"token": t, "kind": k, "first": f, "label": lab} for (t, k, f), lab in zip(found, labels)]


def stratum(o):
    return (o["first"], o["label"]) if o["kind"] == "conjunct" else CONTROL


def draw(pool, need, already, sents, rng, mode):
    """Choose `need` sentences from `pool` (list of row ids), without replacement."""
    if need <= 0 or not pool:
        return []
    if mode == "random":
        return rng.sample(pool, min(need, len(pool)))
    groups = defaultdict(list)
    for s in pool:
        groups[(sents[s]["author"], sents[s]["bin"])].append(s)
    for g in groups.values():
        rng.shuffle(g)
    counts = Counter((sents[s]["author"], sents[s]["bin"]) for s in already)
    chosen = []
    while len(chosen) < need and groups:
        low = min(counts[g] for g in groups)
        g = rng.choice(sorted(k for k in groups if counts[k] == low))
        chosen.append(groups[g].pop())
        counts[g] += 1
        if not groups[g]:
            del groups[g]
    return chosen


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--all-csv", default=ALL_CSV)
    ap.add_argument("--out", default="release")
    ap.add_argument("--per-stratum", type=int, default=200)
    ap.add_argument("--control", type=int, default=200, help="sentences for the non-conjunct control")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--mode", choices=["balanced", "random"], default="balanced")
    ap.add_argument("--length-bins", type=int, default=3)
    ap.add_argument("--min-words", type=int, default=None)
    ap.add_argument("--max-words", type=int, default=None)
    ap.add_argument("--exclude-authors", nargs="*", default=[], help="authors whose text may not be redistributed")
    ap.add_argument("--allow-authors", nargs="*", default=None, help="if given, only these authors are eligible")
    ap.add_argument("--control-allow-conjunct", action="store_true",
                    help="allow control sentences that also contain conjunct ব (default: they may not)")
    ap.add_argument("--list-authors", action="store_true")
    args = ap.parse_args()

    base = pd.read_csv(args.all_csv, keep_default_na=False)
    base.columns = COLUMNS
    if args.list_authors:
        print(base["author"].value_counts().to_string())
        return
    os.makedirs(args.out, exist_ok=True)

    # ---- 1. parse, filter, deduplicate -------------------------------------------------
    permitted = lambda a: (a not in set(args.exclude_authors)) and (args.allow_authors is None or a in set(args.allow_authors))
    counts, corpus_occ, seen, sents = Counter(), Counter(), set(), {}
    for idx, r in enumerate(base.itertuples(index=False)):
        counts["rows"] += 1
        occs = parse_occurrences(r.bengali, r.hindi)
        if occs is None:
            counts["excluded_unpaired"] += 1
            continue
        for o in occs:
            corpus_occ[stratum(o)] += 1
        if not occs:
            counts["no_bengali_ba"] += 1
            continue
        if not permitted(r.author):
            counts["excluded_author"] += 1
            continue
        n_words = len(r.bengali.split())
        if (args.min_words and n_words < args.min_words) or (args.max_words and n_words > args.max_words):
            counts["excluded_length"] += 1
            continue
        key = norm_key(r.bengali)
        if key in seen:
            counts["excluded_duplicate"] += 1
            continue
        seen.add(key)
        sents[idx] = {"author": r.author, "title": r.title, "bengali": r.bengali, "ref": r.hindi,
                      "n_words": n_words, "occ": occs}
    counts["eligible_sentences"] = len(sents)
    if not sents:
        sys.exit("No eligible sentences.")

    # ---- 2. length bins and candidate pools ------------------------------------------
    lengths = np.array([s["n_words"] for s in sents.values()])
    edges = np.quantile(lengths, np.linspace(0, 1, args.length_bins + 1)[1:-1]) if args.length_bins > 1 else np.array([])
    by_stratum = defaultdict(list)
    for idx, s in sents.items():
        s["bin"] = int(np.searchsorted(edges, s["n_words"], side="right")) + 1
        conj = {stratum(o) for o in s["occ"] if o["kind"] == "conjunct"}
        has_iso = any(o["kind"] == "isolated" for o in s["occ"])
        s["strata"] = set(conj)
        if has_iso and (args.control_allow_conjunct or not conj):
            s["strata"].add(CONTROL)
        for k in s["strata"]:
            by_stratum[k].append(idx)

    # ---- 3. draw: rarest stratum first, control last ------------------------------------
    rng = random.Random(args.seed)
    order = sorted((k for k in by_stratum if k != CONTROL), key=lambda k: (len(by_stratum[k]), k))
    if CONTROL in by_stratum:
        order.append(CONTROL)
    selected, drawn = set(), {}
    for key in order:
        quota = args.control if key == CONTROL else args.per_stratum
        cands = sorted(by_stratum[key])
        already = [i for i in cands if i in selected]
        pool = [i for i in cands if i not in selected]
        drawn[key] = draw(pool, quota - len(already), already, sents, rng, args.mode)
        selected.update(drawn[key])
    chosen = sorted(selected)

    # ---- 4. write outputs ------------------------------------------------------------------
    ids = {i: public_id(sents[i]["bengali"]) for i in chosen}
    assert len(set(ids.values())) == len(ids), "public id collision"
    sampled_for = defaultdict(list)
    for key, rows in drawn.items():
        for i in rows:
            sampled_for[i].append(key)
    fmt = lambda k: f"{k[0]}->{k[1]}"

    sent_rows, occ_rows = [], []
    for i in chosen:
        s = sents[i]
        b_tokens, d_tokens = s["bengali"].split(), s["ref"].split()
        aligned = len(b_tokens) == len(d_tokens)
        sent_rows.append({"id": ids[i], "author": s["author"], "title": s["title"], "bengali": s["bengali"],
                          "devanagari_reference": s["ref"], "n_words": s["n_words"], "length_bin": s["bin"],
                          "n_labeled_occurrences": len(s["occ"]),
                          "sampled_for": "; ".join(fmt(k) for k in sorted(sampled_for[i])),
                          "occurrences": "; ".join(f"{o['first'] or 'non-conj'}->{o['label']}" for o in s["occ"])})
        for n, o in enumerate(s["occ"]):
            occ_rows.append({"id": ids[i], "occurrence_index": n, "bengali_word": b_tokens[o["token"]],
                             "devanagari_word": d_tokens[o["token"]] if aligned else "",
                             "position": "conjunct-final" if o["kind"] == "conjunct" else "isolated",
                             "preceding_consonant": o["first"], "label": o["label"],
                             "in_sampled_stratum": stratum(o) in sampled_for[i]})
    pd.DataFrame(sent_rows).to_csv(f"{args.out}/release_sentences.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(occ_rows).to_csv(f"{args.out}/release_occurrences.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame([{"id": ids[i], "corpus_row": i, "author": sents[i]["author"]} for i in chosen]).to_csv(
        f"{args.out}/internal_row_map.csv", index=False, encoding="utf-8-sig")

    report, comp = [], []
    for key in sorted(set(corpus_occ) | set(by_stratum), key=lambda k: (-corpus_occ[k], k)):
        quota = args.control if key == CONTROL else args.per_stratum
        cover = [i for i in chosen if key in sents[i]["strata"]]
        report.append({"preceding_consonant": key[0], "label": key[1], "corpus_occurrences": corpus_occ[key],
                       "eligible_sentences": len(by_stratum.get(key, [])), "quota": quota,
                       "drawn_for_stratum": len(drawn.get(key, [])), "sentences_in_release": len(cover),
                       "labeled_occurrences_in_release": sum(1 for i in chosen for o in sents[i]["occ"] if stratum(o) == key),
                       "shortfall": max(0, quota - len(cover))})
        for a, n in Counter(sents[i]["author"] for i in cover).items():
            comp.append({"preceding_consonant": key[0], "label": key[1], "dimension": "author", "value": a, "sentences": n})
        for b, n in Counter(sents[i]["bin"] for i in cover).items():
            comp.append({"preceding_consonant": key[0], "label": key[1], "dimension": "length_bin", "value": b, "sentences": n})
    rep = pd.DataFrame(report)
    rep.to_csv(f"{args.out}/sampling_report.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(comp).to_csv(f"{args.out}/sampling_report_composition.csv", index=False, encoding="utf-8-sig")

    with open(args.all_csv, "rb") as f:
        checksum = hashlib.sha256(f.read()).hexdigest()
    manifest = {"parameters": {k: v for k, v in vars(args).items() if k not in ("list_authors",)},
                "input_sha256": checksum, "filter_counts": dict(counts),
                "length_bin_edges_words": [float(e) for e in edges],
                "stratum_order": [fmt(k) for k in order],
                "released_sentences": len(chosen), "released_labeled_occurrences": len(occ_rows),
                "python": sys.version.split()[0], "pandas": pd.__version__, "numpy": np.__version__}
    with open(f"{args.out}/manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(json.dumps(dict(counts), indent=1))
    print(f"\nReleased {len(chosen)} sentences containing {len(occ_rows)} labelled occurrences.\n")
    print(rep.to_string(index=False))
    short = rep[rep.shortfall > 0]
    if len(short):
        print(f"\n{len(short)} strata have fewer than their quota of eligible sentences (all were included).")
    print(f"\nFiles written to ./{args.out}/ (do not publish internal_row_map.csv)")


if __name__ == "__main__":
    main()