"""Vigenere encoding and decoding."""

from __future__ import annotations

import string

ALPHABET = string.ascii_lowercase
SIZE = len(ALPHABET)


def _shift(character: str, offset: int, direction: int) -> str:
    base = ord("A") if character.isupper() else ord("a")
    return chr((ord(character) - base + direction * offset) % SIZE + base)


def transform(text: str, key: str, direction: int) -> str:
    """Shift every letter by the key, leaving everything else untouched.

    The key advances only on letters, so punctuation and spacing do not consume
    key positions and the alignment survives any formatting in the ciphertext.
    """
    if not key:
        raise ValueError("the key cannot be empty")
    if any(character not in ALPHABET for character in key):
        raise ValueError("the key must be lowercase letters only")

    output = []
    position = 0
    for character in text:
        if character.isalpha() and character.lower() in ALPHABET:
            offset = ord(key[position % len(key)]) - ord("a")
            output.append(_shift(character, offset, direction))
            position += 1
        else:
            output.append(character)
    return "".join(output)


def encode(plaintext: str, key: str) -> str:
    return transform(plaintext, key, direction=1)


def decode(ciphertext: str, key: str) -> str:
    return transform(ciphertext, key, direction=-1)
