# SALIDtranslit

A small, deterministic transliterator between **Bengali** and **Devanagari** (with **IAST** and **ITRANS** support) that resolves the Bengali *ba/va* ambiguity, plus the evaluation code and the public data release for the accompanying paper.

> Anonymous release for double-blind review. Author names, affiliations and acknowledgements are omitted and will be added after review.

The Bengali letter ব (U+09AC) corresponds to either ब (*ba*) or व (*va*) in Devanagari. Converters that map it to ब everywhere produce the wrong Devanagari wherever a *va* is intended. SALIDtranslit encodes a conjunct-dependent rule for this choice; the paper characterizes the problem on a manually verified corpus of 178,945 sentences and compares the rule against simple repairs.

## What is in this repository

| | |
|---|---|
| `src/salidtranslit/` | the transliteration package |
| `release/` | the public data release: a stratified sample of whole sentences (2,334 sentences, 6,723 labeled occurrences of ব) |
| `evaluate.py`, `metrics.py`, `analysis.py` | evaluation, statistics, and figures |
| `make_release_sample.py` | the script that drew the release sample from the full corpus |

**Not included:** the full 178,945-sentence corpus, which is restricted because of the copyright status of some of its texts. Results that depend on it are reported in the paper as aggregate statistics; see [Reproducing the paper](#reproducing-the-paper) for what can and cannot be recomputed from this repository.

## The rule

Going from Bengali to Devanagari, SALIDtranslit writes ব as व only when it directly follows a virama that follows one of 24 consonants; everywhere else it writes ब. In the other direction, both ब and व map to ব, so there is no decision to make.

The conversion uses a three-state machine (states `s`, `bc`, `v`; initial state `s`). Let *S* be the 24 letters
`ক খ গ ঘ চ ছ জ ঝ ট ঠ ড ঢ ণ ত ৎ থ দ ধ ন ল স শ ষ হ`.

1. If the current character is in *S*, the state becomes `bc`.
2. Otherwise, if the state is `bc` and the character is a virama, the state becomes `v`.
3. Otherwise, if the state is `v` and the character is ব, output व, set the state to `s`, and advance by one character.
4. Otherwise the state becomes `s`.

Unless step 3 applied, the longest match in the Bengali mapping trie is emitted (unmatched characters are copied unchanged), and the scan advances by the length of the match. The machine inspects only the first character of each match, and it requires the consonant, the virama and ব to be adjacent. There is no wordlist or learned component.

In the verified corpus the reference choice depends only on the consonant before the virama: after `স শ দ জ ত ধ হ ছ ন ল থ গ ক ষ ণ খ` the reference always has व, and after `র ম ব য` it always has ब. Eight letters of *S* (`ঘ চ ঝ ট ঠ ড ঢ ৎ`) never precede a virama and ব in the corpus, so the rule's behaviour for them is untested.

## Installation

```bash
git clone https://anonymous.4open.science/r/SALIDtranslit-867A
cd src
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

Tested with Python 3.11. `salidtranslit` itself needs "no third-party packages". The evaluation scripts need the packages in `requirements.txt` (see below).

## Quick start

```python
from salidtranslit import transliterate

transliterate("Bengali", "Devanagari", "বিশ্ব")      # बिश्व   (ব after the conjunct श् -> व)
transliterate("Bengali", "Devanagari", "সর্ব")       # सर्ब    (ব after र् -> ब)
transliterate("Bengali", "Devanagari", "বিলম্ব")     # बिलम्ब  (ব after म् -> ब)
transliterate("Devanagari", "Bengali", "बिश्व")      # বিশ্ব
```

Script names are `"Bengali"`, `"Devanagari"`, `"IAST"` and `"ITRANS"`. The lower-level functions (`ben_dev`, `dev_ben`, `ben_iast`, `ben_itrans`, `dev_iast`, `dev_itrans`, `iast_dev`, `iast_ben`, `itrans_dev`, `itrans_ben`) are in `salidtranslit/core.py`. Only Bengali↔Devanagari is evaluated in the paper.

## Data release

`release/` contains a deliberately stratified sample of whole sentences, not a random sample.

| file | content |
|---|---|
| `release_sentences.csv` | one row per sentence |
| `release_occurrences.csv` | one row per labeled ব in those sentences |
| `sampling_report.csv` | per-category counts in the full corpus, eligible sentences, and the released sample |
| `sampling_report_composition.csv` | author and sentence-length composition of each category |
| `manifest.json` | sampling parameters, random seed, checksum of the input corpus, filter counts |

**`release_sentences.csv` columns:** `id`, `author`, `title`, `bengali`, `devanagari_reference`, `n_words`, `length_bin`, `n_labeled_occurrences`, `sampled_for` (the categories the sentence was drawn for), `occurrences` (the label of every ব in the sentence, in order).

**`release_occurrences.csv` columns:** `id`, `occurrence_index`, `bengali_word`, `devanagari_word` (empty when word counts differ), `position` (`conjunct-final` or `isolated`), `preceding_consonant`, `label` (`ba` or `va`), `in_sampled_stratum`.

**How the sample was drawn.** A category is the consonant immediately before the sequence virama + ব, together with the reference label (20 attested categories, 16 with *va* and four with *ba*), plus a control category of ব outside conjuncts. For each category, up to 200 sentences were drawn without replacement from sentences that are permitted for redistribution, are not exact duplicates, and whose ব count matches the reference's ब/व count. Categories are processed from rarest to most common; within a category, sentences are drawn evenly across author and sentence-length groups. Each sentence is released once with every ব labeled. Because of this design the proportions in the release are **not** natural frequencies (the sample is 30.24% *va* against 6.3% in the full corpus). Natural frequencies from the full corpus are in `sampling_report.csv`.

Only the Bengali sentence, its verified Devanagari reference and the labels are released; the intermediate Devanagari draft produced by an earlier version of the tool is not.

## Reproducing the paper

### Setup

```bash
pip install -r requirements.txt
python -c "import nltk; nltk.download('wordnet')"
git clone https://github.com/anoopkunchukuttan/indic_nlp_resources.git     # METEOR tokenization
```

Packages (see `requirements.txt` for the pinned versions): `aksharamukha` 2.3 (needed only for the evaluation), `salidtranslit` 0.2, `sacrebleu` 2.5.1, `nltk` 3.9.1, `indic-nlp-library` 0.92, `pandas` 2.3.2, `numpy` 2.3.3, `matplotlib` 3.10.8. Everything is deterministic; there are no random seeds in the evaluation.

Each script has path constants at the top (for example `ALL_CSV`, `INDIC_NLP_RESOURCES`, `EVAL_DIR`). Edit them to your paths before running.

### What can be recomputed

| paper item | produced by | needs the full corpus |
|---|---|---|
| Table 2 (positions), Table 3 (preceding consonant), Appendices A and B | `analysis.py` → `figures/table_a_positions.csv`, `table_c_conjunct_types.csv`, `table_b_authors.csv` | yes (the full-corpus category counts are also in `release/sampling_report.csv`) |
| Table 4, Figure 1, Appendix D (other metrics) | `evaluate.py` → `all_scores_summary.csv`, `<direction>_scores.json`; `analysis.py` → `figures/fig1_headline.*` | yes |
| Appendix C (differences unrelated to ba/va) | `review_cases.py` → `review/*.csv` | yes |
| Appendix E (release description and sample results) | `evaluate.py` on the release; `release/sampling_report.csv` | **no** |

### Evaluating on the release sample

`evaluate.py` and `analysis.py` read a five-column CSV by position (author, title, author_title, Bengali, reference). Convert the release first:

```python
import pandas as pd

s = pd.read_csv("release/release_sentences.csv")
pd.DataFrame({
    "author": s.author, "title": s.title, "author_title": s.author + " - " + s.title,
    "bengali": s.bengali, "hindi": s.devanagari_reference,
}).to_csv("release_as_all.csv", index=False)
```

Set `ALL_CSV = "release_as_all.csv"` in `evaluate.py`, then run:

```bash
python evaluate.py          # writes all_scores_summary.csv and <direction>_scores.json
```

The `ben_dev` rows are the Bengali→Devanagari results. Expected decision accuracy on the sample: Aksharamukha 69.76%, all ब→व 30.24%, regex after virama 90.67%, SALIDtranslit 100.0%.

### Full corpus (restricted)

If you have your own copy of a five-column corpus with this schema, the same commands apply:

```bash
python evaluate.py          # all systems, all directions
python analysis.py          # tables A-C, per-author table, figures  -> ./figures
python review_cases.py      # cases for manual review                -> ./review
```

The release itself was produced with `make_release_sample.py`; the exact parameters, seed and input checksum are in `release/manifest.json`. Run `python make_release_sample.py --help` for the options (per-category quota, control size, length bins, excluded or allowed authors, `--seed`).

## Systems and metrics

| system | definition |
|---|---|
| `aksharamukha` | `aksharamukha.transliterate.process("Bengali", "Devanagari", text)`, default options |
| `aksharamukha_naive_va` | the Aksharamukha output with every ब (U+092C) replaced by व (U+0935) |
| `aksharamukha_conjunct_regex` | the Aksharamukha output with every ब directly preceded by a virama (U+094D) replaced by व; pattern `(?<=\u094D)\u092C` |
| `salidtranslit` | `salidtranslit.transliterate("Bengali", "Devanagari", text)` |

**Decision-level (primary):** accuracy, and precision/recall/F1 for *va*, over the ब/व choices. Reference and output ब/व are masked, the strings are aligned with `difflib.SequenceMatcher(autojunk=False)`, and aligned placeholders are compared; unaligned reference decisions count as errors and unaligned output letters as false positives.

**String-level:** exact match (NFC, stripped), CER (corpus-level Levenshtein over code points, in percent), chrF and chrF++ (`sacrebleu`), TER (`sacrebleu`, case-sensitive), BLEU (NLTK, over characters, no smoothing) and METEOR (NLTK with the Indic NLP tokenizer).

**Scales in the output CSV:** BLEU, METEOR and the *va* precision/recall/F1 columns are 0–1; all other columns are 0–100.

## Repository layout

```
src/salidtranslit/     core.py (conversion functions), reference.py (mappings and character sets),
                       trie.py, ScriptMap/*.json (one mapping file per script)
release/               public data release (see above)
evaluate.py            runs the systems and computes the metrics
metrics.py             metric implementations
analysis.py            position and conjunct statistics, per-author table, figures
make_release_sample.py draws the stratified release sample
requirements.txt       pinned package versions
LICENSE                MIT license (code)
```

## Limitations

- The references encode one pronunciation-based convention for when ব becomes व; other conventions would need a different rule.
- The reported agreement is with the references, which began as output of an earlier version of the tool and were corrected by one annotator, so it is not an independent measure of correctness.
- Devanagari→Bengali does not recover khanda ta (ৎ): where the reference has ৎ it writes ত্.
- Only Bengali↔Devanagari is evaluated; the IAST and ITRANS directions are supported but not benchmarked.
- The corpus is 19th- and 20th-century literary text, and most sentences were selected because they contain ব; its statistics are not estimates for Bengali text in general.

## License

- **Code:** [MIT License](LICENSE).
- **Data release:** the verified Devanagari references, labels and sampling metadata are licensed under CC BY-SA 4.0. The underlying Bengali text remains subject to the rights of its authors and sources; the release includes only works whose redistribution is permitted, and excludes Kazi Nazrul Islam, whose works are not yet in the public domain in India. We include a [data card](release/DATACARD.MD) with the release folder. 
- **Third-party tools:** Aksharamukha (AGPL-3.0) is used only as a comparison baseline by `evaluate.py`. It is not part of the `salidtranslit` package and is not included here. Indic NLP Library, sacrebleu and NLTK keep their own licenses.

## Citation
Omitted for double-blind review. Citation will be restored upon acceptance.
