import os
import json
from typing import Dict, List, Set
from . import trie

# JSON mapping files contain: {str: List[str]}
_devanagari: Dict[str, List[str]]
_bengali: Dict[str, List[str]]
_iast: Dict[str, List[str]]
_itrans: Dict[str, List[str]]

_script_dir = os.path.dirname(__file__)
with open(f"{_script_dir}/ScriptMap/devanagari.json", encoding="utf-8") as _dev_json, \
     open(f"{_script_dir}/ScriptMap/bengali.json", encoding="utf-8") as _ben_json, \
     open(f"{_script_dir}/ScriptMap/iast.json", encoding="utf-8") as _iast_json, \
     open(f"{_script_dir}/ScriptMap/itrans.json", encoding="utf-8") as _itrans_json:
    _devanagari = json.load(_dev_json)
    _bengali = json.load(_ben_json)
    _iast = json.load(_iast_json)
    _itrans = json.load(_itrans_json)

# Build tries from mappings
dev_trie: trie.Trie = trie.Trie()
for _term, _mapping in _devanagari.items():
    dev_trie.insert(_term, _mapping)

ben_trie: trie.Trie = trie.Trie()
for _term, _mapping in _bengali.items():
    ben_trie.insert(_term, _mapping)

iast_trie: trie.Trie = trie.Trie()
for _term, _mapping in _iast.items():
    iast_trie.insert(_term, _mapping)

itrans_trie: trie.Trie = trie.Trie()
for _term, _mapping in _itrans.items():
    itrans_trie.insert(_term, _mapping)

# Character sets
end_of_term: Set[str] = {' ', '\n', '\t', '-', '.', ',', '?', '!', "'", '"', 'ঽ', 'ऽ', '(', ')', '[', ']', '{', '}'}

dev_cons: Set[str] = {'क', 'ख', 'ग', 'घ', 'ङ', 'च', 'छ', 'ज', 'झ', 'ञ', 'ट', 'ठ', 'ड', 'ढ', 'ण', 'त', 'थ', 'द', 'ध', 'न', 'प', 'फ', 'ब', 'भ', 'म', 'य', 'र', 'ल', 'व', 'श', 'ष', 'स', 'ह', 'ळ', 'ऴ', 'ऱ', 'ऩ', 'क़', 'ख़', 'ग़', 'ज़', 'ड़', 'ढ़', 'फ़', 'य़'}

ben_b_cons: Set[str] = {'ক', 'খ', 'গ', 'ঘ', 'চ', 'ছ', 'জ', 'ঝ', 'ট', 'ঠ', 'ড', 'ঢ', 'ণ', 'ত', 'ৎ', 'থ', 'দ', 'ধ', 'ন', 'ল', 'স', 'শ', 'ষ', 'হ'}
ben_cons: Set[str] = {'ক', 'খ', 'গ', 'ঘ', 'ঙ', 'চ', 'ছ', 'জ', 'ঝ', 'ঞ', 'ট', 'ঠ', 'ড', 'ঢ', 'ণ', 'ত', 'থ', 'দ', 'ধ', 'ন', 'প', 'ফ', 'ব', 'ভ', 'ম', 'য', 'র', 'ল', 'ভ়', 'শ', 'ষ', 'স', 'হ', 'ল়', 'ষ়', 'র়', 'ন়', 'ক়', 'খ়', 'গ়', 'জ়', 'ড়', 'ঢ়', 'ফ়', 'য়'}

iast_vows: Set[str] = {'a', 'ā', 'i', 'ī', 'u', 'ū', 'ṛ', 'ṝ', 'ḷ', 'ḹ', 'e', 'o', 'ĕ', 'ŏ', 'æ', 'ô', 'm̐', 'ṃ'}
iast_cons: Set[str] = {'k', 'g', 'ṅ', 'c', 'j', 'ñ', 'ṭ', 'ḍ', 'ṇ', 't', 'd', 'n', 'p', 'b', 'm', 'y', 'r', 'l', 'v', 'ś', 'ṣ', 's', 'h', 'l̤', 'ḻ', 'ṟ', 'ṉ', 'q', 'ġ', 'z', 'r̤', 'f', 'ẏ'}

itrans_vows: Set[str] = {'a', 'A', 'i', 'I', 'u', 'U', 'R^', 'L^', 'e', 'o', '^e', '^o', '.N', 'M'}
itrans_cons: Set[str] = {'k', 'g', '~N', 'c', 'C', 'j', '~n', 'T', 'D', 'N', 't', 'd', 'n', 'p', 'b', 'm', 'y', 'r', 'l', 'v', 's', 'S', 'h', 'L', 'z', 'R', '^n', 'q', 'K', 'G', '.D', 'f', 'Y'}