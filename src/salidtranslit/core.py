from __future__ import annotations

from .reference import (
    dev_trie, ben_trie, iast_trie, itrans_trie,
    dev_cons, ben_b_cons, ben_cons,
    end_of_term, iast_vows, iast_cons,
    itrans_vows, itrans_cons
)
from .model import load_finetuned_mt5, correct_transliteration
import re

model: MT5ForConditionalGeneration
tokenizer: MT5Tokenizer
model, tokenizer = load_finetuned_mt5()

def dev_ben(input_str: str) -> str:
    """
    Transliterates Devanagari script to Bengali script using the dev_trie.

    Args:
        input_str (str): Input string in Devanagari script.

    Returns:
        str: Transliterated string in Bengali script.
    """
    output = ""
    i = 0
    while i < len(input_str):
        char = re.sub(r"়|़", "", input_str[i])
        longest_match, match_len = dev_trie.searchLongestMatch(input_str[i:])
        outchar = char
        if longest_match != None:
            outchar = longest_match.rep[0]
            i += match_len
        else:
            i += 1
        output += outchar
    return output

def dev_rom(input_str: str, mode: int) -> str:
    """
    Helper function to transliterate Devanagari to Roman scripts (IAST or ITRANS).

    Args:
        input_str (str): Input string in Devanagari script.
        mode (int): 0 for IAST, 1 for ITRANS.

    Returns:
        str: Transliterated string in Roman script.
    """
    output = ""
    i = 0
    prev, state = "", "s"
    while i < len(input_str):
        char = re.sub(r"‌|়|़", "", input_str[i])
        prev = state
        if char in dev_cons:
            state = "c"
        else:
            state = "s"

        longest_match, match_len = dev_trie.searchLongestMatch(input_str[i:])
        outchar = char
        if longest_match != None:
            outchar = longest_match.rep[1 + mode]
            i += match_len
        else:
            i += 1
        if prev == "c" and (state == "c" or char in end_of_term):
            outchar = "a" + outchar
        output += outchar
    if state == "c":
        output += "a"
    return output

def dev_iast(input_str: str) -> str:
    """
    Transliterates Devanagari script to IAST.

    Args:
        input_str (str): Input string in Devanagari script.

    Returns:
        str: Transliterated string in IAST.
    """
    return dev_rom(input_str, 0)

def dev_itrans(input_str: str) -> str:
    """Transliterates Devanagari script to ITRANS.

    Args:
        input_str (str): Input string in Devanagari script.

    Returns:
        str: Transliterated string in ITRANS.
    """
    return dev_rom(input_str, 1)

def ben_dev(input_str: str) -> str:
    """
    Transliterates Bengali script to Devanagari script.

    Applies heuristic disambiguation and optionally uses a fine-tuned mT5 model
    to correct ambiguous outputs.

    Args:
        input_str (str): Input string in Bengali script.

    Returns:
        str: Transliterated string in Devanagari script.
    """
    output = ""
    i = 0
    state = "s"
    ambiguous = False
    while i < len(input_str):
        char = re.sub(r"়|़", "", input_str[i])
        char = input_str[i]
        if char in ben_b_cons:
            state = "bc"
        elif state == "bc" and char == "্":
            state = "v"
        elif state == "v" and char == "ব":
            char = "व"
            state = "s"
        else:
            state = "s"

        longest_match, match_len = ben_trie.searchLongestMatch(input_str[i:])
        outchar = char
        if outchar != "व" and longest_match != None:
            outchar = longest_match.rep[0]
            i += match_len
        else:
            i += 1
        output += outchar
        if outchar == "ब":
            ambiguous = True

    if ambiguous:
        output = correct_transliteration(input_str, output, model, tokenizer)

    return output

def ben_rom(input_str: str, mode: int) -> str:
    """
    Helper function to transliterate Bengali script to Roman scripts (IAST or ITRANS).

    Args:
        input_str (str): Input string in Bengali script.
        mode (int): 0 for IAST, 1 for ITRANS.

    Returns:
        str: Transliterated string in Roman script.
    """
    output = ""
    i = 0
    prev, state = "", "s"
    while i < len(input_str):
        char = re.sub(r"‌|়|़", "", input_str[i])
        prev = state
        if state != "v" and char in ben_b_cons:
            state = "bc"
        elif state != "v" and char in ben_cons:
            state = "c"
        elif state == "bc" and char == "্":
            state = "v"
        elif state == "v":
            if char == "ব":
                char = "v"
            if char in ben_b_cons:
                state = "bc"
            elif char == "v" or char in ben_cons:
                state = "c"
            else:
                state = "s"
        else:
            state = "s"

        longest_match, match_len = ben_trie.searchLongestMatch(input_str[i:])
        outchar = char
        if outchar != "v" and longest_match != None:
            outchar = longest_match.rep[1 + mode]
            i += match_len
        else:
            i += 1            
        if prev in ("c", "bc") and (state in ("c", "bc") or char in end_of_term):
            outchar = "a" + outchar
        output += outchar
    if state in ("c", "bc"):
        output += "a"
    return output

def ben_iast(input_str: str) -> str:
    """
    Transliterates Bengali script to IAST.

    Args:
        input_str (str): Input string in Bengali script.

    Returns:
        str: Transliterated string in IAST.
    """
    return ben_rom(input_str, 0)

def ben_itrans(input_str: str) -> str:
    """
    Transliterates Bengali script to ITRANS.

    Args:
        input_str (str): Input string in Bengali script.

    Returns:
        str: Transliterated string in ITRANS.
    """
    return ben_rom(input_str, 1)

def iast_ind(input_str: str, mode: int) -> str:
    """
    Helper function to transliterate IAST to Indian scripts (Devanagari or Bengali).

    Args:
        input_str (str): Input string in IAST.
        mode (int): 0 for Devanagari, 1 for Bengali.

    Returns:
        str: Transliterated string in target script.
    """
    output = ""
    i = 0
    prev, state = "", "s"
    while i < len(input_str):
        prev = state
        if input_str[i] in iast_vows:
            if state == "s":
                state = "vow"
            else:
                state = "vs"
        elif input_str[i] in iast_cons:
            state = "c"
        else:
            state = "s"

        longest_match, match_len = iast_trie.searchLongestMatch(input_str[i:])
        if longest_match != None:
            if prev == "c" and state == "c":
                if mode == 0:
                    output += "्" + longest_match.rep[mode][0]
                else:
                    output += "্" + longest_match.rep[mode][0]
            else:
                output += longest_match.rep[mode][0] if state == "vow" else longest_match.rep[mode][-1]
            i += match_len
        else:
            output += input_str[i]
            i += 1
    if state == "c":
        if mode == 0:
            output += "्"
        else:
            output += "্"
    return output

def iast_dev(input_str: str) -> str:
    """
    Transliterates IAST to Devanagari.

    Args:
        input_str (str): Input string in IAST.

    Returns:
        str: Transliterated string in Devanagari script.
    """
    return iast_ind(input_str, 0)

def iast_ben(input_str: str) -> str:
    """
    Transliterates IAST to Bengali.

    Args:
        input_str (str): Input string in IAST.

    Returns:
        str: Transliterated string in Bengali script.
    """
    return iast_ind(input_str, 1)

def itrans_ind(input_str: str, mode: int) -> str:
    """
    Helper function to transliterate ITRANS to Indian scripts (Devanagari or Bengali).

    Args:
        input_str (str): Input string in ITRANS.
        mode (int): 0 for Devanagari, 1 for Bengali.

    Returns:
        str: Transliterated string in target script.
    """
    output = ""
    i = 0
    prev, state = "", "s"
    while i < len(input_str):
        prev = state
        if input_str[i] in itrans_vows or input_str[i:i+2] in itrans_vows:
            if state == "s":
                state = "vow"
            else:
                state = "vs"
        elif input_str[i] in itrans_cons or input_str[i:i+2] in itrans_cons:
            state = "c"
        else:
            state = "s"

        longest_match, match_len = itrans_trie.searchLongestMatch(input_str[i:])
        if longest_match != None:
            if prev == "c" and state == "c":
                if mode == 0:
                    output += "्" + longest_match.rep[mode][0]
                else:
                    output += "্" + longest_match.rep[mode][0]
            else:
                output += longest_match.rep[mode][0] if state == "vow" else longest_match.rep[mode][-1]
            i += match_len
        else:
            output += input_str[i]
            i += 1

    if state == "c":
        if mode == 0:
            output += "्"
        else:
            output += "্"
    return output

def itrans_dev(input_str: str) -> str:
    """
    Transliterates ITRANS to Devanagari.

    Args:
        input_str (str): Input string in ITRANS.

    Returns:
        str: Transliterated string in Devanagari script.
    """
    return itrans_ind(input_str, 0)

def itrans_ben(input_str: str) -> str:
    """
    Transliterates ITRANS to Bengali.

    Args:
        input_str (str): Input string in ITRANS.

    Returns:
        str: Transliterated string in Bengali script.
    """
    return itrans_ind(input_str, 1)