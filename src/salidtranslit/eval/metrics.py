"""
metrics.py -- extra evaluation metrics for SALIDtranslit.

Kept separate from evaluate.py so these functions can be imported and tested
without needing salidtranslit / aksharamukha / indicnlp installed.

Dependencies
------------
  required : sacrebleu   (already used by evaluate.py)
  optional : rapidfuzz   (makes CER ~100x faster; falls back to pure Python)
"""

import re
import unicodedata
from collections import Counter
from difflib import SequenceMatcher

try:
    from rapidfuzz.distance import Levenshtein as _Levenshtein

    def _edit_distance(a, b):
        return _Levenshtein.distance(a, b)

except ImportError:  # pure-Python fallback (two-row DP)
    def _edit_distance(a, b):
        if a == b:
            return 0
        if not a:
            return len(b)
        if not b:
            return len(a)
        prev = list(range(len(b) + 1))
        for i, ca in enumerate(a, 1):
            cur = [i]
            for j, cb in enumerate(b, 1):
                cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
            prev = cur
        return prev[-1]


def _norm(s):
    """NFC-normalize so that visually identical strings compare equal."""
    return unicodedata.normalize("NFC", s)


# --------------------------------------------------------------------------
# Generic string-level metrics
# --------------------------------------------------------------------------

def corpus_ter(expected, predicted):
    """
    Corpus-level TER via sacrebleu.

    NOTE the reference shape: sacrebleu expects a list of reference *streams*,
    i.e. [[ref_1, ref_2, ..., ref_N]] for a single reference per sentence.
    Passing [[ref_1], [ref_2], ...] makes sacrebleu treat the data as N
    references for ONE sentence.

    case_sensitive=True matters for ITRANS/IAST, where case carries meaning
    (e.g. ITRANS 'A' = long a); sacrebleu's TER default is case-insensitive.

    Returns a dict so callers can sanity-check ref_length (it should equal the
    total number of whitespace-separated words in `expected`).
    """
    from sacrebleu.metrics import TER

    score = TER(case_sensitive=True).corpus_score(list(predicted), [list(expected)])
    return {
        "score": score.score,
        "num_edits": score.num_edits,
        "ref_length": score.ref_length,
    }


def corpus_chrf(expected, predicted, word_order=0):
    """chrF (word_order=0) or chrF++ (word_order=2). Scale: 0-100."""
    from sacrebleu.metrics import CHRF

    return CHRF(word_order=word_order).corpus_score(list(predicted), [list(expected)]).score


def corpus_cer(expected, predicted):
    """
    Corpus-level character error rate, in percent (0-100, can exceed 100):
    total Levenshtein edits / total reference characters.

    Characters are Unicode code points, not grapheme clusters, so a Bengali
    conjunct such as 'স্ব' counts as three characters (consonant, virama,
    consonant). This is consistent across systems, but state it in the paper.
    """
    edits = 0
    ref_chars = 0
    for e, p in zip(expected, predicted):
        e, p = _norm(e), _norm(p)
        edits += _edit_distance(e, p)
        ref_chars += len(e)
    return 100.0 * edits / ref_chars if ref_chars else 0.0


def exact_match(expected, predicted):
    """Percentage of sentences transliterated with zero errors (NFC, stripped)."""
    pairs = list(zip(expected, predicted))
    hits = sum(_norm(e).strip() == _norm(p).strip() for e, p in pairs)
    return 100.0 * hits / len(pairs) if pairs else 0.0


# --------------------------------------------------------------------------
# Task-specific metric: scoring the ba/va decision itself
# --------------------------------------------------------------------------

# Devanagari target classes. Every ब/व in the *Devanagari* reference comes from
# the single Bengali letter ব (U+09AC), so each occurrence is one ba/va decision.
BA_VA_CLASSES = {"ba": "\u092C", "va": "\u0935"}   # ब , व

_PLACEHOLDER = "\uE000"  # private-use code point; never occurs in the data


def naive_ba_to_va(text):
    """The 'just replace every ba with va' strawman, applied to Devanagari."""
    return text.replace(BA_VA_CLASSES["ba"], BA_VA_CLASSES["va"])


_CONJUNCT_BA = re.compile("(?<=\u094D)\u092C")


def conjunct_ba_to_va(text):
    """
    Output-side regex baseline: in Devanagari text, turn every ब that directly
    follows a virama into व.
    """
    return _CONJUNCT_BA.sub("\u0935", text)


def _align_decisions(ref, pred, chars):
    """
    Align the target characters of `ref` to those of `pred`.

    Both strings are masked (every target char -> one placeholder) so that a
    ba-vs-va disagreement does not disturb the alignment; difflib then aligns
    the masked strings. Returns:
      pairs     : [(ref_char, pred_char | None)] for each target char in ref
                  (None = could not be aligned, e.g. deleted by other edits)
      spurious  : [pred_char] for target chars in pred aligned to nothing in ref
    """
    mref = "".join(_PLACEHOLDER if c in chars else c for c in ref)
    mpred = "".join(_PLACEHOLDER if c in chars else c for c in pred)

    ref_to_pred = {}
    for a, b, size in SequenceMatcher(None, mref, mpred, autojunk=False).get_matching_blocks():
        for k in range(size):
            ref_to_pred[a + k] = b + k

    pairs, used_pred = [], set()
    for i, c in enumerate(ref):
        if c in chars:
            j = ref_to_pred.get(i)
            if j is None:
                pairs.append((c, None))
            else:
                pairs.append((c, pred[j]))
                used_pred.add(j)
    spurious = [c for j, c in enumerate(pred) if c in chars and j not in used_pred]
    return pairs, spurious


def decision_scores(expected, predicted, classes=BA_VA_CLASSES):
    """
    Score only the positions where a contrast decision (e.g. ba vs va) is made.

    Unaligned reference decisions count as errors (false negatives for their
    true class); unaligned predicted target chars count as false positives, so
    a system cannot score well by simply dropping or adding characters.

    Returns decision accuracy, per-class precision/recall/F1, macro-F1, and the
    fraction of sentences in which every decision is correct.
    """
    chars = set(classes.values())
    name_of = {v: k for k, v in classes.items()}
    tp, fp, fn, support = Counter(), Counter(), Counter(), Counter()
    n_decisions = n_correct = n_unaligned = n_spurious = 0
    n_sent = n_sent_clean = 0

    for ref, pred in zip(expected, predicted):
        pairs, spurious = _align_decisions(_norm(ref), _norm(pred), chars)
        if not pairs:
            continue
        n_sent += 1
        clean = not spurious
        for r, p in pairs:
            n_decisions += 1
            support[name_of[r]] += 1
            if p is None:
                n_unaligned += 1
                fn[name_of[r]] += 1
                clean = False
            elif r == p:
                n_correct += 1
                tp[name_of[r]] += 1
            else:
                fn[name_of[r]] += 1
                fp[name_of[p]] += 1
                clean = False
        for p in spurious:
            n_spurious += 1
            fp[name_of[p]] += 1
        n_sent_clean += clean

    per_class = {}
    for name in classes:
        prec = tp[name] / (tp[name] + fp[name]) if (tp[name] + fp[name]) else 0.0
        rec = tp[name] / (tp[name] + fn[name]) if (tp[name] + fn[name]) else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
        per_class[name] = {"precision": prec, "recall": rec, "f1": f1, "support": support[name]}

    return {
        "n_decisions": n_decisions,
        "decision_accuracy": 100.0 * n_correct / n_decisions if n_decisions else 0.0,
        "n_unaligned": n_unaligned,
        "n_spurious": n_spurious,
        "macro_f1": sum(c["f1"] for c in per_class.values()) / len(per_class),
        "sentence_all_correct": 100.0 * n_sent_clean / n_sent if n_sent else 0.0,
        "per_class": per_class,
    }