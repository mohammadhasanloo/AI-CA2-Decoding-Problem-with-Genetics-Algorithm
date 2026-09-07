"""Command line entry point: ``python -m vigenere.cli ...``"""

from __future__ import annotations

import argparse
import json
import random
import time
from pathlib import Path

from vigenere.corpus import load_vocabulary
from vigenere.figures import fitness_curve
from vigenere.genetic import KeySearch

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DOCS = ROOT / "docs"
RESULTS = ROOT / "results"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ciphertext", type=Path, default=DATA / "encoded_text.txt")
    parser.add_argument("--reference", type=Path, default=DATA / "reference_text.txt")
    parser.add_argument("--key-length", type=int, default=14)
    parser.add_argument("--population", type=int, default=60)
    parser.add_argument("--generations", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--figure", type=Path, default=DOCS / "fitness.png")
    parser.add_argument("--results", type=Path, default=RESULTS)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    ciphertext = args.ciphertext.read_text(encoding="utf-8", errors="ignore")
    search = KeySearch(
        ciphertext,
        load_vocabulary(args.reference),
        key_length=args.key_length,
        population_size=args.population,
        rng=random.Random(args.seed),
    )

    started = time.perf_counter()
    result = search.run(max_generations=args.generations)
    elapsed = time.perf_counter() - started

    if result.solved:
        print(f"key recovered: {result.key}")
        print(f"{len(result.generations)} generations, {elapsed:.1f}s\n")
        print(result.plaintext[:400])
    else:
        best = result.generations[-1]
        print(f"not solved in {args.generations} generations")
        print(f"best key {best.best_key} scoring {best.best_fitness}")

    fitness_curve(result.generations, args.figure, result.key)
    args.results.mkdir(parents=True, exist_ok=True)
    (args.results / "run.json").write_text(
        json.dumps(
            {
                "key": result.key,
                "solved": result.solved,
                "generations": len(result.generations),
                "seconds": round(elapsed, 2),
                "key_length": args.key_length,
                "population": args.population,
                "seed": args.seed,
                "best_fitness": result.generations[-1].best_fitness,
            },
            indent=2,
        )
        + "\n"
    )
    return 0 if result.solved else 1


if __name__ == "__main__":
    raise SystemExit(main())
