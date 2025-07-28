from typing import Dict, List, Optional, Tuple

class TrieNode:
    """
    A node in the Trie structure.

    Attributes:
        children (Dict[str, TrieNode]): Dictionary mapping characters to child TrieNodes.
        end_of_term (bool): Flag indicating whether this node terminates a valid key.
        rep (List[str]): Representation list associated with the key.
    """
    def __init__(self) -> None:
        self.children: Dict[str, TrieNode] = {}
        self.end_of_term: bool = False
        self.rep: List[str] = []

class Trie:
    """
    A Trie data structure for storing and searching key sequences.

    Methods:
        insert(key: str, rep_list: List[str]) -> None:
            Inserts a key with its representation list into the trie.

        searchLongestMatch(key: str) -> Tuple[Optional[TrieNode], int]:
            Searches for the longest matching prefix in the trie.
    """
    def __init__(self) -> None:
        self.root: TrieNode = TrieNode()

    def insert(self, key: str, rep_list: List[str]) -> None:
        """
        Insert a key into the Trie with its corresponding representation list.

        Args:
            key (str): The input string key.
            rep_list (List[str]): The list of strings representing the value.
        """
        curr = self.root
        for c in key:
            if c not in curr.children:
                curr.children[c] = TrieNode()
            curr = curr.children[c]
        curr.end_of_term = True
        curr.rep = rep_list

    def searchLongestMatch(self, key: str) -> Tuple[Optional[TrieNode], int]:
        """
        Search for the longest matching prefix in the Trie.

        Args:
            key (str): The input string to match.

        Returns:
            Tuple[Optional[TrieNode], int]: The TrieNode of the longest match and its length.
        """
        curr = self.root
        longest_match: Optional[TrieNode] = None
        match_len: int = 0

        if key and key[0] in ("়", "़"):  # Nukta handling
            return longest_match, match_len

        for i, c in enumerate(key):
            if c not in curr.children:
                break
            curr = curr.children[c]
            if curr.end_of_term:
                longest_match = curr
                match_len = i + 1

        return longest_match, match_len