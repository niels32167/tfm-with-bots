"""Checks Prices against Recorded Games (ticket 11): what a Production step, a Terraform Rating step, a
card or a kept MegaCredit was worth in Victory Points at the end, by the Generations then left.

    uv run python -m ai.recorded_games.price_check
    uv run python -m ai.recorded_games.price_check --min-rating 500 --no-prelude

For each position the dataset holds (one per Research phase, after its Production phase), it takes the
difference between the two Players and regresses the final Victory Point margin on it by least squares,
one fit per number of Generations left. Differences cancel what both Players share, such as how long
the Game ran. A coefficient is Victory Points at the end per unit of a thing then; it is printed beside
the Card Economy Bot's Prices at the same Generations left, also in Victory Points (a Price over the
Price of a Victory Point).

These are associations, not causes: a Player ahead in Production at Generation 3 was often the better
Player, so the coefficients run high. They are a check, never Prices themselves (spec, "Prices").
"""

import argparse
import math
from collections import defaultdict
from collections.abc import Iterable
from typing import Any

from ai.prices import DEFAULT, RESOURCES, Prices
from ai.recorded_games.dataset import read_games

# What is regressed on, each as the Player's count less the other Player's.
FEATURES = (
    [f"{resource} kept" for resource in RESOURCES]
    + [f"{resource} Production" for resource in RESOURCES]
    + ["Terraform Rating", "cards played", "science Tags", "hand"]
)


def features(position: dict[str, Any], player: int) -> list[float] | None:
    """The Player's position less the other Player's, or None where the log left a value unknown."""
    me, other = position["players"][player], position["players"][1 - player]

    def of(board: dict[str, Any]) -> list[float]:
        return (
            [board["resources"][r] for r in RESOURCES]
            + [board["production"][r] for r in RESOURCES]
            + [board["terraform_rating"], len(board["played"]), board["tags"].get("science", 0), board["hand_counter"]]
        )

    mine, others = of(me), of(other)
    if None in mine or None in others:
        return None
    return [a - b for a, b in zip(mine, others, strict=True)]


def rows(games: Iterable[dict[str, Any]], min_rating: int, prelude: bool) -> dict[int, list[tuple[list[float], float]]]:
    """The regression rows by Generations left: the Player's position less the other's, and the final
    Victory Point margin. Each Game gives both Players' rows."""
    by_left: dict[int, list[tuple[list[float], float]]] = defaultdict(list)
    for game in games:
        players = game["players"]
        if game["conceded"] or game["prelude"] != prelude or min(p["rating"] or 0 for p in players) < min_rating:
            continue
        for position in game["positions"][1:]:
            left = game["generations"] - position["generation"] + 1
            for player in (0, 1):
                difference = features(position, player)
                if difference is not None:
                    margin = players[player]["victory_points"] - players[1 - player]["victory_points"]
                    by_left[left].append((difference, margin))
    return by_left


def least_squares(rows: list[tuple[list[float], float]], ridge: float = 1e-3) -> list[float]:
    """The coefficients minimising the squared error, with no intercept (the differences are symmetric),
    by the normal equations and Gaussian elimination; a little ridge keeps unused features at 0."""
    size = len(rows[0][0])
    matrix = [[0.0] * size for _ in range(size)]
    vector = [0.0] * size
    for x, y in rows:
        for i in range(size):
            vector[i] += x[i] * y
            row = matrix[i]
            for j in range(size):
                row[j] += x[i] * x[j]
    for i in range(size):
        matrix[i][i] += ridge * len(rows)
    for column in range(size):
        pivot = max(range(column, size), key=lambda r: abs(matrix[r][column]))
        matrix[column], matrix[pivot] = matrix[pivot], matrix[column]
        vector[column], vector[pivot] = vector[pivot], vector[column]
        for r in range(size):
            if r != column and matrix[column][column]:
                factor = matrix[r][column] / matrix[column][column]
                matrix[r] = [a - factor * b for a, b in zip(matrix[r], matrix[column], strict=True)]
                vector[r] -= factor * vector[column]
    return [vector[i] / matrix[i][i] if matrix[i][i] else 0.0 for i in range(size)]


def bot_prices(left: int) -> list[float]:
    """The Card Economy Bot's Prices with `left` Generations left, in Victory Points, in FEATURES' order.
    Read from an empty position: Prices that depend on the cards held use no context."""
    view = {
        "temperature": -30,
        "oxygen": 0,
        "oceans": 0,
        "generation": 1,
        "players": [
            {"hand": [], "card_costs": {}, "tags": {}, "played_cards": [], "corporation": None, "production": {}},
        ],
    }
    prices = Prices(view, 0, float(left), DEFAULT)
    point = prices.victory_point()
    return [
        *[prices.megacredit() / point] + [prices.resource(r) / point for r in RESOURCES[1:]],
        *[prices.production(r) / point for r in RESOURCES],
        prices.terraform_rating() / point,
        float("nan"),
        prices.tag("science") / point,
        prices.card_drawn() * DEFAULT.holding / point,
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--min-rating", type=int, default=400, help="the lower Player's least rating (400)")
    parser.add_argument("--no-prelude", action="store_true", help="Games without Prelude instead")
    parser.add_argument("--most-left", type=int, default=12, help="the most Generations left to fit (12)")
    arguments = parser.parse_args()

    by_left = rows(read_games(), arguments.min_rating, not arguments.no_prelude)
    print(f"Final Victory Point margin on position differences; lower rating {arguments.min_rating}+,")
    print(f"{'without' if arguments.no_prelude else 'with'} Prelude. Each cell: Recorded Games / the Bot's Prices,")
    print("in Victory Points at the end per unit then.\n")
    lefts = [left for left in sorted(by_left) if left <= arguments.most_left and len(by_left[left]) >= 200]
    fits = {left: least_squares(by_left[left]) for left in lefts}
    print(f"{'Generations left':>22}" + "".join(f"{left:>12}" for left in lefts))
    print(f"{'positions':>22}" + "".join(f"{len(by_left[left]) // 2:>12,}" for left in lefts))
    for index, name in enumerate(FEATURES):
        cells = []
        for left in lefts:
            bot = bot_prices(left)[index]
            cells.append(
                f"{fits[left][index]:5.2f}/{bot:<5.2f}" if not math.isnan(bot) else f"{fits[left][index]:5.2f}/  -  "
            )
        print(f"{name:>22}" + "".join(f"{cell:>12}" for cell in cells))
    print("\nA kept MegaCredit's coefficient is Victory Points per MegaCredit; its inverse, the MegaCredits a")
    print("Victory Point was worth then:")
    print(
        f"{'Recorded Games':>22}"
        + "".join(f"{1 / fits[left][0] if fits[left][0] > 0 else float('inf'):>12.1f}" for left in lefts)
    )
    print(f"{'the Bot':>22}" + "".join(f"{1 / bot_prices(left)[0]:>12.1f}" for left in lefts))


if __name__ == "__main__":
    main()
