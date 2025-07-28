from __future__ import annotations

from transformers import MT5ForConditionalGeneration, MT5Tokenizer
import torch
import os
import unicodedata
from nltk.metrics.distance import edit_distance
from typing import Tuple

_script_dir = os.path.dirname(__file__)
def load_finetuned_mt5(model_path: str = f"{_script_dir}/mt5_finetuned") -> Tuple[MT5ForConditionalGeneration, MT5Tokenizer]:
    """
    Loads the fine-tuned mT5 model and tokenizer for inference.
    """
    model = MT5ForConditionalGeneration.from_pretrained(model_path)
    tokenizer = MT5Tokenizer.from_pretrained(model_path)
    return model, tokenizer

_nukta_map = {
    'क': 'क़',
    'ख': 'ख़',
    'ग': 'ग़',
    'ज': 'ज़',
    'ड': 'ड़',
    'ढ': 'ढ़',
    'फ': 'फ़',
    'य': 'य़',
}
def correct_transliteration(bengali: str, partial_trans: str, model: MT5ForConditionalGeneration, tokenizer: MT5Tokenizer) -> str:
    """
    Generates corrected transliteration from the input Bengali and partial transliteration.
    """
    prompt = f"""Task: Correct the transliteration of the following Bengali sentence. The partial transliteration may contain misspellings.
Bengali: {bengali}
Partial transliteration: {partial_trans}
Correct transliteration:
"""
    device = "cuda" if torch.cuda.is_available() else "cpu"

    model.to(device)
    inputs = tokenizer(prompt, return_tensors="pt").to(device)

    outputs = model.generate(
        **inputs,
        max_new_tokens=256,
        num_beams=5,
        early_stopping=True,
    )

    corrected_trans = tokenizer.decode(outputs[0], skip_special_tokens=True)

    if "Correct transliteration:" in corrected_trans:
        index = corrected_trans.index("Correct transliteration:") + len("Correct transliteration:") + 1
        corrected_trans = corrected_trans[index:]

    corrected_trans_norm = unicodedata.normalize('NFC', corrected_trans)
    corrected_trans = ""
    for i in range(len(corrected_trans_norm) - 1):
        if corrected_trans_norm[i] == "़":
            continue
        elif corrected_trans_norm[i] in _nukta_map and corrected_trans_norm[i + 1] == "़":
            corrected_trans += _nukta_map[corrected_trans_norm[i]]
        else:
            corrected_trans += corrected_trans_norm[i]

    edit = edit_distance(corrected_trans, partial_trans)
    rep_count = partial_trans.count("ब")
    if edit > rep_count:
        corrected_trans = partial_trans

    return corrected_trans