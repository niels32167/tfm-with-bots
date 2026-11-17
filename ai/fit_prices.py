"""Fits the Card Economy Bot's Prices by Matches (ticket 11), with a separable CMA-ES.

    uv run python -m ai.fit_prices --generations 20 --population 12 --games 160
    uv run python -m ai.fit_prices --generations 2 --population 4 --games 20     # a quick try

Each weight is searched as the logarithm of its share of the starting weight (`ai.prices.DEFAULT`), so
a step means the same for every weight. Each generation of the search, every candidate plays the
starting Card Economy Bot on the same fresh seeds, each seed both ways; its fitness is its win rate
plus its mean Victory Point margin over 200, which lowers the noise (spec, "Models"). The mean of the
search and its history are written to --out after every generation, and the best mean is printed as
Python for `Weights`.

It keeps every core busy for as long as it runs: about 1 to 2 hours with the first line's settings.
"""

import argparse
import dataclasses
import functools
import json
import math
import random
import time
from pathlib import Path

from ai.card_economy import CardEconomyBot
from ai.match import run_match
from ai.prices import DEFAULT, Weights

OUT = Path(__file__).parents[1] / ".cache" / "price-fit.json"

# Weights held below an upper bound, so that the search can't make nonsense of them.
UPPER = {"discount": 0.97, "victory_point_decay": 1.0, "end_megacredit": 1.0, "conversion": 1.0, "holding": 1.2}

# Seeds the search plays on, well away from those Matches are reported on.
FIRST_SEED = 1_000_000


class SeparableCMAES:
    """The CMA-ES with a diagonal covariance (Ros and Hansen, 2008): for minimising a noisy function of a
    few dozen numbers from its values alone. `ask` gives points to try and `tell` takes their values,
    lower being better."""

    def __init__(self, mean: list[float], step: float, population: int, random_numbers: random.Random) -> None:
        n = len(mean)
        self.mean = list(mean)
        self.step = step
        self.population = population
        self.random = random_numbers
        self.parents = population // 2
        raw = [math.log(self.parents + 0.5) - math.log(i + 1) for i in range(self.parents)]
        self.recombination = [w / sum(raw) for w in raw]
        self.mu_eff = 1 / sum(w * w for w in self.recombination)
        self.c_sigma = (self.mu_eff + 2) / (n + self.mu_eff + 5)
        self.d_sigma = 1 + 2 * max(0.0, math.sqrt((self.mu_eff - 1) / (n + 1)) - 1) + self.c_sigma
        self.c_c = (4 + self.mu_eff / n) / (n + 4 + 2 * self.mu_eff / n)
        separable = (n + 2) / 3
        self.c_1 = min(1.0, separable * 2 / ((n + 1.3) ** 2 + self.mu_eff))
        self.c_mu = min(
            1 - self.c_1, separable * 2 * (self.mu_eff - 2 + 1 / self.mu_eff) / ((n + 2) ** 2 + self.mu_eff)
        )
        self.expected_norm = math.sqrt(n) * (1 - 1 / (4 * n) + 1 / (21 * n * n))
        self.variances = [1.0] * n
        self.path_sigma = [0.0] * n
        self.path_c = [0.0] * n
        self.generation = 0
        self.drawn: dict[tuple[float, ...], list[float]] = {}

    def ask(self) -> list[list[float]]:
        points = []
        self.drawn = {}
        for _ in range(self.population):
            z = [self.random.gauss(0.0, 1.0) for _ in self.mean]
            point = [m + self.step * math.sqrt(v) * zi for m, v, zi in zip(self.mean, self.variances, z, strict=True)]
            self.drawn[tuple(point)] = z
            points.append(point)
        return points

    def tell(self, points: list[list[float]], losses: list[float]) -> None:
        n = len(self.mean)
        best = sorted(range(len(points)), key=losses.__getitem__)[: self.parents]
        zs = [self.drawn[tuple(points[i])] for i in best]
        ys = [[math.sqrt(v) * zi for v, zi in zip(self.variances, z, strict=True)] for z in zs]
        z_mean = [sum(w * z[j] for w, z in zip(self.recombination, zs, strict=True)) for j in range(n)]
        y_mean = [sum(w * y[j] for w, y in zip(self.recombination, ys, strict=True)) for j in range(n)]
        self.mean = [m + self.step * y for m, y in zip(self.mean, y_mean, strict=True)]
        scale = math.sqrt(self.c_sigma * (2 - self.c_sigma) * self.mu_eff)
        self.path_sigma = [(1 - self.c_sigma) * p + scale * z for p, z in zip(self.path_sigma, z_mean, strict=True)]
        norm = math.sqrt(sum(p * p for p in self.path_sigma))
        self.generation += 1
        held = (
            norm / math.sqrt(1 - (1 - self.c_sigma) ** (2 * self.generation)) < (1.4 + 2 / (n + 1)) * self.expected_norm
        )
        scale_c = math.sqrt(self.c_c * (2 - self.c_c) * self.mu_eff) if held else 0.0
        self.path_c = [(1 - self.c_c) * p + scale_c * y for p, y in zip(self.path_c, y_mean, strict=True)]
        self.variances = [
            (1 - self.c_1 - self.c_mu) * v
            + self.c_1 * pc * pc
            + self.c_mu * sum(w * y[j] * y[j] for w, y in zip(self.recombination, ys, strict=True))
            for j, (v, pc) in enumerate(zip(self.variances, self.path_c, strict=True))
        ]
        self.step *= math.exp(self.c_sigma / self.d_sigma * (norm / self.expected_norm - 1))


def weights_at(point: list[float]) -> Weights:
    """The weights at a point of the search: each the starting weight times e to its coordinate, held
    below its upper bound."""
    numbers = {}
    for field, start, x in zip(dataclasses.fields(Weights), DEFAULT.vector(), point, strict=True):
        weight = start * math.exp(x)
        numbers[field.name] = min(weight, UPPER[field.name]) if field.name in UPPER else weight
    return Weights(**numbers)


def fitness(weights: Weights, games: int, first_seed: int) -> tuple[float, float, float]:
    """How a Card Economy Bot with `weights` does against the starting one: its fitness, win rate and
    mean Victory Point margin."""
    match = run_match(
        "candidate",
        "start",
        games,
        first_seed=first_seed,
        makers=(functools.partial(CardEconomyBot, weights), CardEconomyBot),
    )
    candidate, start = match.sides
    margin = candidate.mean_points - start.mean_points
    return candidate.score + margin / 200, candidate.score, margin


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--generations", type=int, default=20)
    parser.add_argument("--population", type=int, default=12)
    parser.add_argument("--games", type=int, default=160, help="Games per candidate, even")
    parser.add_argument("--step", type=float, default=0.25, help="the first step, in log-shares of a weight")
    parser.add_argument("--seed", type=int, default=11, help="for the search's random numbers")
    parser.add_argument("--out", type=Path, default=OUT)
    arguments = parser.parse_args()

    search = SeparableCMAES(
        [0.0] * len(DEFAULT.vector()), arguments.step, arguments.population, random.Random(arguments.seed)
    )
    history = []
    for generation in range(arguments.generations):
        started = time.time()
        seed = FIRST_SEED + generation * arguments.games
        points = search.ask()
        results = [fitness(weights_at(point), arguments.games, seed) for point in points]
        search.tell(points, [-result[0] for result in results])
        mean_result = fitness(weights_at(search.mean), arguments.games, seed + 500_000)
        history.append(
            {
                "generation": generation,
                "best": max(results),
                "mean_of_candidates": sum(r[1] for r in results) / len(results),
                "search_mean": mean_result,
                "step": search.step,
                "weights": dataclasses.asdict(weights_at(search.mean)),
            }
        )
        arguments.out.parent.mkdir(parents=True, exist_ok=True)
        arguments.out.write_text(json.dumps(history, indent=1))
        _, rate, margin = mean_result
        print(
            f"generation {generation + 1}: candidates won {history[-1]['mean_of_candidates']:.1%} on average, "
            f"best {max(r[1] for r in results):.1%}; the mean won {rate:.1%} by {margin:+.1f} points; "
            f"step {search.step:.3f} ({time.time() - started:.0f} s)",
            flush=True,
        )
    print("\nThe search's mean, as Weights:")
    print(repr(weights_at(search.mean)))


if __name__ == "__main__":
    main()
