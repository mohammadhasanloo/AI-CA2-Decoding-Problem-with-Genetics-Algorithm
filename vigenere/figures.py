"""Plotting how fitness climbs across generations."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from vigenere.genetic import Generation  # noqa: E402

BEST_COLOUR = "#1a7f37"
MEAN_COLOUR = "#0969da"


def fitness_curve(history: list[Generation], output_path: Path, key: str | None = None) -> Path:
    """Best and mean fitness per generation."""
    generations = [record.index for record in history]
    figure, axis = plt.subplots(figsize=(9, 4.2))
    axis.plot(generations, [r.best_fitness for r in history], label="best in population",
              color=BEST_COLOUR, linewidth=2)
    axis.plot(generations, [r.mean_fitness for r in history], label="population mean",
              color=MEAN_COLOUR, linewidth=1.4, alpha=0.8)

    axis.set_xlabel("generation")
    axis.set_ylabel("recognised words")
    axis.grid(alpha=0.3)
    axis.legend(loc="lower right")
    title = f"Fitness across {len(history)} generations"
    if key:
        title += f", key recovered: {key}"
    axis.set_title(title, fontsize=12)

    figure.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=140)
    plt.close(figure)
    return output_path
