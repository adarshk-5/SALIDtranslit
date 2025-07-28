from __future__ import annotations

from .core import (
    ben_dev, ben_iast, ben_itrans,
    dev_ben, dev_iast, dev_itrans,
    iast_dev, iast_ben,
    itrans_dev, itrans_ben
)

def transliterate(source: str, target: str, text: str) -> str:
    """
    Transliterates a string `text` from the `source` script to the `target` script.

    This function uses pre-built Trie structures for each supported script to match
    and replace terms from the source script with their corresponding representations
    in the target script.

    Supported scripts: 'devanagari', 'bengali', 'iast', 'itrans'

    Args:
        source (str): The source script name (e.g. "devanagari", "iast").
        target (str): The target script name (e.g. "bengali", "itrans").
        text (str): The input text to transliterate.

    Returns:
        str: The transliterated string in the target script.

    Raises:
        ValueError: If the source or target script is not supported.

    Example:
        >>> transliterate("iast", "bengali", "viśva")
        'বিশ্ব'
    """
    source, target = source.lower().strip(), target.lower().strip()

    accepted = {"bengali", "devanagari", "iast", "itrans"}
    roman = {"iast", "itrans"}

    if source not in accepted or target not in accepted:
        raise ValueError("Unrecognized input")
    elif source == target or (source in roman and target in roman):
        raise ValueError("Invalid input combination")

    if source == "bengali":
        return {
            "devanagari": ben_dev,
            "iast": ben_iast,
            "itrans": ben_itrans,
        }[target](text)
    if source == "devanagari":
        return {
            "bengali": dev_ben,
            "iast": dev_iast,
            "itrans": dev_itrans,
        }[target](text)
    if source == "iast":
        return {
            "devanagari": iast_dev,
            "bengali": iast_ben,
        }[target](text)
    if source == "itrans":
        return {
            "devanagari": itrans_dev,
            "bengali": itrans_ben,
        }[target](text)
    return text