# SALIDtranslit

A small, deterministic transliterator between **Bengali** and **Devanagari** (with **IAST** and **ITRANS** support) that resolves the Bengali *ba/va* ambiguity: the Bengali letter ব (U+09AC) is written ब or व in Devanagari depending on context. The repository also contains the evaluation code and analysis scripts for the accompanying paper.

> Anonymous release for double-blind review. Author names, affiliations and acknowledgements are omitted and will be added after review.

## What it does

Going from Bengali to Devanagari, SALIDtranslit writes ব as व only when it directly follows a virama that follows one of 24 consonants; everywhere else it writes ब. In the verified corpus described below, this reproduces the reference choice for every one of the 381,234 occurrences of ব. In the other direction, both ब and व map to ব.

```python
from salidtranslit import transliterate

transliterate("Bengali", "Devanagari", "বিশ্ব")   # बिश्व   (ব after the conjunct श् -> व)
transliterate("Bengali", "Devanagari", "সর্ব")    # सर्ब    (ব after र् -> ब)
transliterate("Devanagari", "Bengali", "बिश्व")   # বিশ্ব
```

Script names are `"Bengali"`, `"Devanagari"`, `"IAST"` and `"ITRANS"`. The lower-level functions (`ben_dev`, `dev_ben`, `ben_iast`, `ben_itrans`, `dev_iast`, `dev_itrans`, `iast_dev`, `iast_ben`, `itrans_dev`, `itrans_ben`) are in `salidtranslit/core.py`.

The rule, in the state machine used by `ben_dev` (states `s`, `bc`, `v`; initial state `s`). Let *S* be the 24 letters
`ক খ গ ঘ চ ছ জ ঝ ট ঠ ড ঢ ণ ত ৎ থ দ ধ ন ল স শ ষ হ`.

1. If the current character is in *S*, the state becomes `bc`.
2. Otherwise, if the state is `bc` and the character is a virama, the state becomes `v`.
3. Otherwise, if the state is `v` and the character is ব, output व, set the state to `s`, and advance by one character.
4. Otherwise the state becomes `s`.

Unless step 3 applied, the longest match in the Bengali mapping trie is emitted (unmatched characters are copied). Consonant, virama and ব must be adjacent. There is no wordlist or learned component. Eight letters of *S* never precede a virama and ব in the corpus (ঘ চ ঝ ট ঠ ড ঢ ৎ), so the rule's behaviour for them is untested.

## Installation

```bash
git clone https://anonymous.4open.science/r/SALIDtranslit-867A/
cd src
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

Python 3.11. Dependencies of the package itself can be found in `requirements.txt`.

## Repository layout

```
src/salidtranslit/      package: core.py (conversion functions), reference.py (loads mappings, character sets),
                        trie.py, ScriptMap/*.json (one mapping file per script)
data/all.csv            the verified corpus (see below)
evaluate.py             runs the systems and computes all metrics
metrics.py              metric implementations used by evaluate.py and analysis.py
analysis.py             position/conjunct statistics, per-author table, figures
requirements.txt        pinned versions of the packages used for the paper
```

## Data

`data/all.csv` has 178,945 rows, one sentence per row, with five columns in this order:

| column | content |
|---|---|
| `author` | author name |
| `title` | work title |
| `author_title` | author and title |
| `bengali` | the Bengali sentence |
| `hindi` | the corrected, verified Devanagari reference |

The scripts read the file by column position, so keep the order. The corpus contains literary works by eight authors: 174,934 sentences selected because they contain ব, and 4,011 unfiltered sentences. 

[TODO: sources of the texts; how sentences were segmented; who verified the references and how; license and what is released; if the texts cannot be redistributed, how to rebuild the corpus]

## Reproducing the paper

### 1. Environment

```bash
pip install -r requirements.txt
python -c "import nltk; nltk.download('wordnet')"
git clone https://github.com/anoopkunchukuttan/indic_nlp_resources.git     # used for METEOR tokenization
```

Packages used: `aksharamukha` 2.3, `salidtranslit` 0.2, `sacrebleu`, `nltk`, `indic-nlp-library`, `pandas`, `numpy`, `matplotlib`; `rapidfuzz` is optional and makes CER much faster. 

### 2. Set the paths

Edit the constants at the top of `evaluate.py` and `analysis.py`:

| constant | meaning |
|---|---|
| `ALL_CSV` | path to `data/all.csv` |
| `EVAL_DIR` | folder of cached `*_eval.csv` files (only used if `USE_CACHED_EVAL_CSVS = True`) |
| `INDIC_NLP_RESOURCES` | path to the cloned `indic_nlp_resources` |
| `AKSHARAMUKHA_BAVA_OPTION` | leave `None` unless you have confirmed Aksharamukha's built-in ba/va option name |

### 3. Run

```bash
python evaluate.py        # all systems, all directions (~1-2 hour runtime)
python analysis.py        # tables and figures
```

All computation is deterministic; there are no random seeds. Set `USE_CACHED_EVAL_CSVS = False` (the default) whenever the data or the set of systems changes.

### 4. Outputs and where they appear in the paper

| script | writes | used for |
|---|---|---|
| `evaluate.py` | `all_scores_summary.csv`, `<direction>_scores.json`, `<direction>_eval.csv` | main results table, Appendix on other metrics |
| `analysis.py` | `figures/fig1_headline.{pdf,png}` | Figure 1 |
| `analysis.py` | `figures/table_a_positions.csv` | position table (ba/va by position of ব) |
| `analysis.py` | `figures/table_c_conjunct_types.csv`, `figures/fig4_conjunct_types.*` | preceding-consonant table and appendix |
| `analysis.py` | `figures/table_b_authors.csv`, `figures/fig3_authors.*` | per-author appendix table |

### Systems compared

| name | definition |
|---|---|
| `aksharamukha` | `aksharamukha.transliterate.process("Bengali", "Devanagari", text)`, default options |
| `aksharamukha_naive_va` | the Aksharamukha output with every ब (U+092C) replaced by व (U+0935) |
| `aksharamukha_conjunct_regex` | the Aksharamukha output with every ब directly preceded by a virama (U+094D) replaced by व; pattern `(?<=\u094D)\u092C` |
| `salidtranslit` | `salidtranslit.transliterate("Bengali", "Devanagari", text)` |

### Metrics

Decision-level (primary): accuracy, and precision/recall/F1 for *va*, over the ब/व choices. Reference and output ब/व are masked, the strings are aligned with `difflib.SequenceMatcher(autojunk=False)`, and aligned placeholders are compared. Unaligned reference decisions count as errors and unaligned output letters as false positives.

String-level: exact match (NFC, stripped), CER (corpus-level Levenshtein over code points, in percent), chrF and chrF++ (`sacrebleu`), TER (`sacrebleu`, case-sensitive), BLEU (NLTK, computed over characters, no smoothing), and METEOR (NLTK with the Indic NLP tokenizer). Scales in the CSV: BLEU, METEOR and the *va* precision/recall/F1 columns are 0–1; all other columns are 0–100.

## Known limitations

- The references encode one pronunciation-based convention for when ব becomes व; other conventions would need a different rule.
- The reported agreement is with the references, which were produced from an earlier version of the tool and corrected by one annotator, so it is not an independent measure of correctness.
- Devanagari→Bengali does not recover khanda ta (ৎ): where the reference has ৎ it writes ত্ (7,481 spans in the corpus).
- Only Bengali↔Devanagari is evaluated; the IAST and ITRANS directions are supported but not benchmarked.

## License

The code in this repository is released under the [MIT License](LICENSE).
 
The corpus in `data/` is **not** covered by the MIT license. [TODO: data license and availability; the texts are literary works whose copyright status varies by author]
 
Aksharamukha (released under AGPL-3.0) is used only as a comparison baseline by `evaluate.py`. It is not part of the `salidtranslit` package and is not included in this repository; install it separately (see Installation) to run the evaluation. Other third-party tools (Indic NLP Library, sacrebleu, NLTK) keep their own licenses.