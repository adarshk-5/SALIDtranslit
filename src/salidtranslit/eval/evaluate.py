from salidtranslit import *
from aksharamukha import transliterate as akshar_trans
import pandas

# import nltk
# nltk.download('wordnet')
from nltk.translate.bleu_score import corpus_bleu
from nltk.translate.meteor_score import single_meteor_score
import numpy as np

import json
import time

from indicnlp import common
from indicnlp import loader

from metrics import (
    BA_VA_CLASSES,
    corpus_cer,
    corpus_chrf,
    conjunct_ba_to_va,
    corpus_ter,
    decision_scores,
    exact_match,
    naive_ba_to_va,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
# REPLACE THE FOLLOWING WITH YOUR LOCAL FILEPATHS
INDIC_NLP_RESOURCES = None
ALL_CSV = None
EVAL_DIR = None

# Name of Aksharamukha's built-in Bengali ba->va post-processing option.
AKSHARAMUKHA_BAVA_OPTION = None

# False -> recompute every system output from all.csv (required whenever the
# dataset or the set of systems changes). True -> reuse the cached *_eval.csv
# files in EVAL_DIR, which will NOT contain any newly added system columns.
USE_CACHED_EVAL_CSVS = False

common.set_resources_path(INDIC_NLP_RESOURCES)
loader.load()

from indicnlp.tokenize import indic_tokenize


def corpus_meteor(expected, predicted):
    def tokenize(sentence):
        return indic_tokenize.trivial_tokenize(sentence, lang='hi')
    meteor_score_sentences_list = [single_meteor_score(tokenize(expect), tokenize(predict)) for expect, predict in zip(expected, predicted)]
    meteor_score_res = np.mean(meteor_score_sentences_list)
    return meteor_score_res


base_eval = pandas.read_csv(ALL_CSV)

# Load eval_set_final.csv for dev/ben
    # df.apply function to create new df
    #   input, eval_output, aksharamukha_output, salid_output
    # repeat for dev->ben and ben->dev
    # calculate bleu, meteor, and ter for aksharamukha and salid by comparing respective outputs to eval_output


def ind_prepare(input, eval_output, source, target, bava=False):
    """
    Run every system on one sentence and return a named Series (so the columns
    of the resulting DataFrame are created automatically).

    bava=True (Bengali -> Devanagari only) adds the ba/va strawmen:
      * aksharamukha_naive_va : Aksharamukha's default output with every
                                ब replaced by व after the fact
      * aksharamukha_conjunct_regex : Aksharamukha's default output with every
                                ब that follows a virama replaced by व
      * aksharamukha_bava_mode: Aksharamukha's own option, if configured
    """
    row = {"input": input, "eval_output": eval_output}

    start = time.perf_counter()
    aksharamukha_output = akshar_trans.process(source, target, input)
    aksharamukha_time = time.perf_counter() - start
    row["aksharamukha_output"] = aksharamukha_output
    row["aksharamukha_time"] = aksharamukha_time

    if bava:
        start = time.perf_counter()
        naive_output = naive_ba_to_va(aksharamukha_output)
        row["aksharamukha_naive_va_output"] = naive_output
        row["aksharamukha_naive_va_time"] = aksharamukha_time + (time.perf_counter() - start)

        start = time.perf_counter()
        regex_output = conjunct_ba_to_va(aksharamukha_output)
        row["aksharamukha_conjunct_regex_output"] = regex_output
        row["aksharamukha_conjunct_regex_time"] = aksharamukha_time + (time.perf_counter() - start)

        if AKSHARAMUKHA_BAVA_OPTION:
            start = time.perf_counter()
            row["aksharamukha_bava_mode_output"] = akshar_trans.process(
                source, target, input, post_options=[AKSHARAMUKHA_BAVA_OPTION])
            row["aksharamukha_bava_mode_time"] = time.perf_counter() - start

    start = time.perf_counter()
    salid_output = transliterate(source, target, input)
    salid_time = time.perf_counter() - start
    row["salid_output"] = salid_output
    row["salid_time"] = salid_time

    # print(salid_output)
    return pandas.Series(row)

def ben_dev_prepare(row):
    vals = row.values
    author, title, author_title, bengali, hindi = vals
    return ind_prepare(bengali, hindi, "Bengali", "Devanagari", bava=True)

def dev_ben_prepare(row):
    vals = row.values
    author, title, author_title, bengali, hindi = vals
    return ind_prepare(hindi, bengali, "Devanagari", "Bengali")

# use aksharamukha to romanize ben and dev from eval_set_final.csv
    # df.apply function to create new df
    #   input, aksharamukha_output, salid_output
    # repeat for dev->iast, dev->itrans, iast->dev, itrans->dev 
    # repeat for ben->iast, ben->itrans, iast->ben, itrans->ben
    # calculate bleu, meteor, and ter by comparing salid to aksharamukha

def ind_rom_prepare(input, source, target):
    eval_output = akshar_trans.process(source, target, input)

    start = time.perf_counter()
    salid_output = transliterate(source, target, input)
    salid_time = time.perf_counter() - start

    return [input, eval_output, salid_output, salid_time]

def ben_iast_prepare(row):
    vals = row.values
    author, title, author_title, bengali, hindi = vals
    return ind_rom_prepare(bengali, "Bengali", "IAST")

def ben_itrans_prepare(row):
    vals = row.values
    author, title, author_title, bengali, hindi = vals
    return ind_rom_prepare(bengali, "Bengali", "ITRANS")

def dev_iast_prepare(row):
    vals = row.values
    author, title, author_title, bengali, hindi = vals
    return ind_rom_prepare(hindi, "Devanagari", "IAST")

def dev_itrans_prepare(row):
    vals = row.values
    author, title, author_title, bengali, hindi = vals
    return ind_rom_prepare(hindi, "Devanagari", "ITRANS")

def iast_ben_prepare(row):
    vals = row.values
    eval_output, input, _1, _2 = vals

    start = time.perf_counter()
    salid_output = transliterate("IAST", "Bengali", input)
    salid_time = time.perf_counter() - start

    return [input, eval_output, salid_output, salid_time]

def itrans_ben_prepare(row):
    vals = row.values
    eval_output, input, _1, _2 = vals

    start = time.perf_counter()
    salid_output = transliterate("ITRANS", "Bengali", input)
    salid_time = time.perf_counter() - start

    return [input, eval_output, salid_output, salid_time]

def iast_dev_prepare(row):
    vals = row.values
    eval_output, input, _1, _2 = vals

    start = time.perf_counter()
    salid_output = transliterate("IAST", "Devanagari", input)
    salid_time = time.perf_counter() - start

    return [input, eval_output, salid_output, salid_time]

def itrans_dev_prepare(row):
    vals = row.values
    eval_output, input, _1, _2 = vals

    start = time.perf_counter()
    salid_output = transliterate("ITRANS", "Devanagari", input)
    salid_time = time.perf_counter() - start

    return [input, eval_output, salid_output, salid_time]


# ---------------------------------------------------------------------------
# Build (or load) every evaluation DataFrame
# ---------------------------------------------------------------------------
ROM_COLUMNS = ["input", "eval_output", "salid_output", "salid_time"]

if USE_CACHED_EVAL_CSVS:
    names = ["ben_dev", "dev_ben", "ben_iast", "ben_itrans", "dev_iast",
             "dev_itrans", "iast_ben", "itrans_ben", "iast_dev", "itrans_dev"]
    eval_sets = {n: pandas.read_csv(f"{EVAL_DIR}{n}_eval.csv") for n in names}
else:
    ben_dev_eval = base_eval.apply(ben_dev_prepare, axis=1)
    dev_ben_eval = base_eval.apply(dev_ben_prepare, axis=1)

    ben_iast_eval = base_eval.apply(ben_iast_prepare, axis=1, result_type='expand')
    ben_itrans_eval = base_eval.apply(ben_itrans_prepare, axis=1, result_type='expand')
    dev_iast_eval = base_eval.apply(dev_iast_prepare, axis=1, result_type='expand')
    dev_itrans_eval = base_eval.apply(dev_itrans_prepare, axis=1, result_type='expand')
    for df in (ben_iast_eval, ben_itrans_eval, dev_iast_eval, dev_itrans_eval):
        df.columns = ROM_COLUMNS

    iast_ben_eval = ben_iast_eval.apply(iast_ben_prepare, axis=1, result_type='broadcast')
    itrans_ben_eval = ben_itrans_eval.apply(itrans_ben_prepare, axis=1, result_type='broadcast')
    iast_dev_eval = dev_iast_eval.apply(iast_dev_prepare, axis=1, result_type='broadcast')
    itrans_dev_eval = dev_itrans_eval.apply(itrans_dev_prepare, axis=1, result_type='broadcast')

    eval_sets = {
        "ben_dev": ben_dev_eval, "dev_ben": dev_ben_eval,
        "ben_iast": ben_iast_eval, "ben_itrans": ben_itrans_eval,
        "dev_iast": dev_iast_eval, "dev_itrans": dev_itrans_eval,
        "iast_ben": iast_ben_eval, "itrans_ben": itrans_ben_eval,
        "iast_dev": iast_dev_eval, "itrans_dev": itrans_dev_eval,
    }


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------
# (name, output column, time column). Systems whose columns are missing from a
# given DataFrame are skipped automatically.
SYSTEMS = [
    ("aksharamukha",          "aksharamukha_output",          "aksharamukha_time"),
    ("aksharamukha_naive_va", "aksharamukha_naive_va_output", "aksharamukha_naive_va_time"),
    ("aksharamukha_conjunct_regex", "aksharamukha_conjunct_regex_output", "aksharamukha_conjunct_regex_time"),
    ("aksharamukha_bava_mode", "aksharamukha_bava_mode_output", "aksharamukha_bava_mode_time"),
    ("salidtranslit",         "salid_output",                 "salid_time"),
]


def score_system(expected, predicted):
    expected_bleu = [[item] for item in expected]
    ter = corpus_ter(expected, predicted)
    return {
        "bleu": corpus_bleu(expected_bleu, predicted),
        "meteor": corpus_meteor(expected, predicted),
        "ter": ter["score"],
        "ter_num_edits": ter["num_edits"],
        "ter_ref_length": ter["ref_length"],   # sanity check: ~ total words in `expected`
        "chrf": corpus_chrf(expected, predicted, word_order=0),
        "chrf++": corpus_chrf(expected, predicted, word_order=2),
        "cer": corpus_cer(expected, predicted),
        "exact_match": exact_match(expected, predicted),
    }


def evaluate(df, direction, ba_va_decisions=False):
    print(direction)
    output = {}
    expected = df["eval_output"].to_list()
    for name, out_col, time_col in SYSTEMS:
        if out_col not in df.columns:
            continue
        predicted = df[out_col].to_list()
        result = score_system(expected, predicted)
        if ba_va_decisions:
            result["ba_va_decisions"] = decision_scores(expected, predicted, BA_VA_CLASSES)
        result["summary_stats"] = df[time_col].astype("float64").describe().to_dict()
        output[name] = result
    with open(f'{direction}_scores.json', 'w') as f:
        json.dump(output, f, ensure_ascii=False, indent=4)
    return output


all_scores = {}
for direction, df in eval_sets.items():
    # ba/va decisions only exist where the *target* is Devanagari and the source
    # is Bengali; in Devanagari -> Bengali, va and ba both map to the single ব.
    all_scores[direction] = evaluate(df, direction, ba_va_decisions=(direction == "ben_dev"))

# One flat table for the paper: direction x system x metric
METRIC_KEYS = ["bleu", "meteor", "ter", "chrf", "chrf++", "cer", "exact_match"]
rows = []
for direction, systems in all_scores.items():
    for system, res in systems.items():
        row = {"direction": direction, "system": system}
        row.update({k: res[k] for k in METRIC_KEYS})
        if "ba_va_decisions" in res:
            d = res["ba_va_decisions"]
            row.update({
                "bava_decision_acc": d["decision_accuracy"],
                "bava_macro_f1": d["macro_f1"],
                "va_precision": d["per_class"]["va"]["precision"],
                "va_recall": d["per_class"]["va"]["recall"],
                "va_f1": d["per_class"]["va"]["f1"],
            })
        rows.append(row)
summary = pandas.DataFrame(rows)
summary.to_csv("all_scores_summary.csv", index=False)
print(summary.to_string(index=False))

for direction, df in eval_sets.items():
    df.to_csv(f"{direction}_eval.csv", index=False)