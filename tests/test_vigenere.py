"""Tests for the cipher, the vocabulary and the search."""

from __future__ import annotations

import random

import pytest

from vigenere.cipher import decode, encode
from vigenere.corpus import vocabulary, words
from vigenere.genetic import KeySearch

PLAINTEXT = "the quick brown fox jumps over the lazy dog"
KEY = "lemon"


def test_encoding_then_decoding_returns_the_original():
    assert decode(encode(PLAINTEXT, KEY), KEY) == PLAINTEXT


def test_encoding_changes_the_text():
    assert encode(PLAINTEXT, KEY) != PLAINTEXT


def test_case_and_punctuation_survive_a_round_trip():
    text = "Attack at Dawn, on the 5th! (no delay)"
    assert decode(encode(text, KEY), KEY) == text


def test_the_key_advances_only_on_letters():
    """Spacing must not consume key positions, or alignment drifts."""
    assert encode("ab", "ab") == encode("a b", "ab").replace(" ", "")


def test_a_key_of_a_leaves_the_text_unchanged():
    assert encode(PLAINTEXT, "a") == PLAINTEXT


@pytest.mark.parametrize("bad", ["", "AB", "a1", "a b"])
def test_invalid_keys_are_rejected(bad):
    with pytest.raises(ValueError):
        encode(PLAINTEXT, bad)


def test_words_splits_on_anything_non_alphabetic():
    assert words("Hello, world! 42 times") == ["hello", "world", "times"]


def test_vocabulary_is_the_distinct_words():
    assert vocabulary("the cat the dog") == {"the", "cat", "dog"}


def test_fitness_counts_recognised_words():
    known = vocabulary(PLAINTEXT)
    search = KeySearch(encode(PLAINTEXT, KEY), known, len(KEY), rng=random.Random(0))
    assert search.fitness(KEY) == len(words(PLAINTEXT))


def test_the_correct_key_scores_higher_than_a_wrong_one():
    known = vocabulary(PLAINTEXT)
    search = KeySearch(encode(PLAINTEXT, KEY), known, len(KEY), rng=random.Random(0))
    assert search.fitness(KEY) > search.fitness("zzzzz")


def test_a_partially_correct_key_scores_partially():
    """Fitness must reward getting some positions right, or there is no gradient
    for the search to climb."""
    known = vocabulary(PLAINTEXT)
    search = KeySearch(encode(PLAINTEXT, KEY), known, len(KEY), rng=random.Random(0))
    assert 0 < search.fitness("lemoz") < search.fitness(KEY)


def test_solved_only_when_every_word_is_recognised():
    known = vocabulary(PLAINTEXT)
    search = KeySearch(encode(PLAINTEXT, KEY), known, len(KEY), rng=random.Random(0))
    assert search.is_solved(KEY)
    assert not search.is_solved("zzzzz")


def test_crossover_preserves_length_and_alphabet():
    search = KeySearch(encode(PLAINTEXT, KEY), vocabulary(PLAINTEXT), 8,
                       crossover_rate=1.0, rng=random.Random(1))
    first, second = search.crossover("aaaaaaaa", "bbbbbbbb")
    for child in (first, second):
        assert len(child) == 8
        assert set(child) <= {"a", "b"}


def test_crossover_children_recombine_both_parents():
    search = KeySearch(encode(PLAINTEXT, KEY), vocabulary(PLAINTEXT), 8,
                       crossover_rate=1.0, rng=random.Random(2))
    first, second = search.crossover("aaaaaaaa", "bbbbbbbb")
    assert "b" in first and "a" in second


def test_a_zero_crossover_rate_passes_parents_through():
    search = KeySearch(encode(PLAINTEXT, KEY), vocabulary(PLAINTEXT), 8,
                       crossover_rate=0.0, rng=random.Random(3))
    assert search.crossover("aaaaaaaa", "bbbbbbbb") == ("aaaaaaaa", "bbbbbbbb")


def test_a_zero_mutation_rate_leaves_a_key_alone():
    search = KeySearch(encode(PLAINTEXT, KEY), vocabulary(PLAINTEXT), 5,
                       mutation_rate=0.0, rng=random.Random(4))
    assert search.mutate("lemon") == "lemon"


def test_a_full_mutation_rate_changes_every_position_it_can():
    search = KeySearch(encode(PLAINTEXT, KEY), vocabulary(PLAINTEXT), 5,
                       mutation_rate=1.0, rng=random.Random(5))
    assert search.mutate("lemon") != "lemon"


def test_the_best_candidate_never_regresses():
    """Elitism: the top of one generation is carried into the next."""
    search = KeySearch(encode(PLAINTEXT, KEY), vocabulary(PLAINTEXT), len(KEY),
                       rng=random.Random(6))
    best = 0
    for _ in range(8):
        search.step()
        current = max(search.fitness(key) for key in search.population)
        assert current >= best
        best = current


@pytest.mark.parametrize("bad_length", [0, 1])
def test_key_length_must_be_usable(bad_length):
    with pytest.raises(ValueError):
        KeySearch("abc", set(), bad_length)


def test_the_search_recovers_a_short_key():
    text = " ".join([PLAINTEXT] * 4)
    known = vocabulary(text)
    search = KeySearch(encode(text, "key"), known, 3, population_size=80,
                       rng=random.Random(7))
    result = search.run(max_generations=400)
    assert result.solved
    assert result.plaintext == text


def test_an_unsolvable_search_reports_rather_than_looping():
    search = KeySearch("qqqq", {"nothing"}, 4, rng=random.Random(8))
    result = search.run(max_generations=5)
    assert not result.solved
    assert len(result.generations) == 5
