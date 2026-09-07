"""Searching for the key with a genetic algorithm.

The key is never derived analytically. A population of candidate keys is scored
by how much English the decoding produces, and the best are recombined. Fitness
is a count of recognised words, which rises smoothly as a key gets closer to
correct: getting one position right makes every letter at that offset decode
correctly, so partial keys score partially.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from vigenere.cipher import ALPHABET, decode
from vigenere.corpus import words

DEFAULT_POPULATION = 60
DEFAULT_ELITE_FRACTION = 0.2
DEFAULT_CROSSOVER_RATE = 0.65
DEFAULT_MUTATION_RATE = 0.1


@dataclass
class Generation:
    index: int
    best_key: str
    best_fitness: int
    mean_fitness: float
    solved: bool


@dataclass
class Result:
    key: str | None
    plaintext: str | None
    generations: list[Generation] = field(default_factory=list)

    @property
    def solved(self) -> bool:
        return self.key is not None


class KeySearch:
    """A population of candidate keys, evolved against a reference vocabulary."""

    def __init__(
        self,
        ciphertext: str,
        vocabulary: set[str],
        key_length: int,
        population_size: int = DEFAULT_POPULATION,
        elite_fraction: float = DEFAULT_ELITE_FRACTION,
        crossover_rate: float = DEFAULT_CROSSOVER_RATE,
        mutation_rate: float = DEFAULT_MUTATION_RATE,
        rng: random.Random | None = None,
    ):
        if key_length < 2:
            raise ValueError("key length must be at least 2")
        if population_size < 2:
            raise ValueError("population must hold at least two candidates")

        self.ciphertext = ciphertext
        self.vocabulary = vocabulary
        self.key_length = key_length
        self.population_size = population_size
        self.elite_size = max(2, int(population_size * elite_fraction))
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.rng = rng or random.Random()
        self.population = [self._random_key() for _ in range(population_size)]

    def _random_key(self) -> str:
        return "".join(self.rng.choice(ALPHABET) for _ in range(self.key_length))

    def fitness(self, key: str) -> int:
        """How many decoded words are real words."""
        return sum(word in self.vocabulary for word in words(decode(self.ciphertext, key)))

    def is_solved(self, key: str) -> bool:
        decoded = words(decode(self.ciphertext, key))
        return bool(decoded) and all(word in self.vocabulary for word in decoded)

    def crossover(self, first: str, second: str) -> tuple[str, str]:
        """Two-point crossover: the middle segment is swapped between parents."""
        if self.key_length < 3 or self.rng.random() >= self.crossover_rate:
            return first, second
        left = self.rng.randint(1, self.key_length - 2)
        right = self.rng.randint(1, self.key_length - 1)
        left, right = min(left, right), max(left, right)
        return (
            first[:left] + second[left:right] + first[right:],
            second[:left] + first[left:right] + second[right:],
        )

    def mutate(self, key: str) -> str:
        """Replace each position with an independent probability."""
        return "".join(
            self.rng.choice(ALPHABET) if self.rng.random() < self.mutation_rate else character
            for character in key
        )

    def step(self) -> list[str]:
        """One generation: rank, keep the elite, breed the rest from them."""
        ranked = sorted(self.population, key=self.fitness, reverse=True)
        elite = ranked[: self.elite_size]

        # The best candidate is carried through unchanged, so a generation can
        # never score worse than the one before it.
        offspring = [elite[0]]
        while len(offspring) < self.population_size:
            first, second = self.rng.sample(elite, 2)
            for child in self.crossover(first, second):
                if len(offspring) < self.population_size:
                    offspring.append(self.mutate(child))

        self.population = offspring
        return ranked

    def run(self, max_generations: int = 1000, on_generation=None) -> Result:
        history: list[Generation] = []
        for index in range(max_generations):
            ranked = self.step()
            scores = [self.fitness(key) for key in ranked]
            best = ranked[0]
            record = Generation(
                index=index,
                best_key=best,
                best_fitness=scores[0],
                mean_fitness=sum(scores) / len(scores),
                solved=self.is_solved(best),
            )
            history.append(record)
            if on_generation:
                on_generation(record)
            if record.solved:
                return Result(best, decode(self.ciphertext, best), history)
        return Result(None, None, history)
