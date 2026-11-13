"""Tables computed from the dataset, to compare with the spec's counts ("What we measured") and with
tfmstats.com's tables (the spec's "Statistics from tfmstats.com").

    uv run python -m ai.recorded_games.tables
    uv run python -m ai.recorded_games.tables --out .cache/recorded-games --least-offered 200

Unless told otherwise, the setup, Corporation, Prelude Card, Milestone and Award tables use Games with
Prelude, as tfmstats.com's Starting Hand page does (2 Players, Tharsis, Prelude and the Draft, no Colonies).
Never use these tables, or tfmstats.com's, as training data or model inputs: they include held-out Games.
"""

import argparse
import sys
from collections.abc import Callable, Iterable, Sequence
from pathlib import Path
from typing import Any

from ai.recorded_games.dataset import DATASET_FOLDER, read_games

type Game = dict[str, Any]


def setups(games: Iterable[Game]) -> Iterable[tuple[Game, dict[str, Any]]]:
    for game in games:
        for decision in game["decisions"]:
            if decision["kind"] == "setup":
                yield game, decision


def keep_rates(games: Iterable[Game]) -> dict[str, tuple[int, int]]:
    """For each Project Card offered at setup: how often it was offered, and how often kept."""
    rates: dict[str, tuple[int, int]] = {}
    for _, setup in setups(games):
        kept = set(setup["picked"]["cards"])
        for card in setup["offer"]["cards"]:
            offered, taken = rates.get(card, (0, 0))
            rates[card] = (offered + 1, taken + (card in kept))
    return rates


def chosen_table(
    games: Iterable[Game], offered_key: str, picked: Callable[[dict[str, Any]], list[str]]
) -> dict[str, dict[str, int]]:
    table: dict[str, dict[str, int]] = {}
    for game, setup in setups(games):
        won = game["players"][setup["player"]]["winner"]
        chosen = set(picked(setup["picked"]))
        for card in setup["offer"][offered_key]:
            row = table.setdefault(card, {"offered": 0, "chosen": 0, "won": 0})
            row["offered"] += 1
            if card in chosen:
                row["chosen"] += 1
                row["won"] += won
    return table


def corporation_table(games: Iterable[Game]) -> dict[str, dict[str, int]]:
    """For each Corporation: how often it was dealt, chosen, and chosen by the winner."""
    return chosen_table(games, "corporations", lambda picked: [picked["corporation"]])


def prelude_table(games: Iterable[Game]) -> dict[str, dict[str, int]]:
    """For each Prelude Card: how often it was dealt, kept, and kept by the winner."""
    return chosen_table(games, "prelude_cards", lambda picked: picked["prelude_cards"])


def claims_table(games: Iterable[Game], kind: str, key: str) -> dict[str, dict[str, Any]]:
    """For each Milestone ("milestones", "milestone") or Award ("awards", "award"): how often it was
    claimed or funded, the mean Generation it happened in, and how often by the Game's winner."""
    table: dict[str, dict[str, Any]] = {}
    generations: dict[str, list[float]] = {}
    for game in games:
        for claim in game.get(kind) or []:
            row = table.setdefault(claim[key], {"claimed": 0, "mean_generation": None, "won": 0})
            row["claimed"] += 1
            row["won"] += game["players"][claim["player"]]["winner"]
            if claim["generation"] is not None:
                generations.setdefault(claim[key], []).append(claim["generation"])
    for name, row in table.items():
        row["mean_generation"] = mean(generations.get(name, []))
    return table


def mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def card_points(player: dict[str, Any]) -> int | None:
    return (player["points"] or {}).get("cards")


def both_rated(games: list[Game], floor: int) -> int:
    """How many of the Games have both Players rated at least `floor`."""
    return sum(all(isinstance(p["rating"], int) and p["rating"] >= floor for p in game["players"]) for game in games)


def spec_counts(games: Iterable[Game]) -> dict[str, dict[str, Any]]:
    """The spec's table of Recorded Games, by Prelude: Games, those not conceded, those whose lower-rated
    Player is rated at least 450, 500 or 600, and over Games not conceded, the mean Generations, the
    winner's and loser's mean Victory Points, and the mean card Victory Points of the winner and of the
    Player with more (the spec's "better Player")."""
    split: dict[str, list[Game]] = {"Prelude": [], "no Prelude": []}
    for game in games:
        split["Prelude" if game["prelude"] else "no Prelude"].append(game)
    counts = {}
    for setting, found in split.items():
        played = [game for game in found if not game["conceded"]]

        finished = [game for game in played if sum(p["winner"] for p in game["players"]) == 1]
        winners = [next(p for p in game["players"] if p["winner"]) for game in finished]
        losers = [next(p for p in game["players"] if not p["winner"]) for game in finished]
        counts[setting] = {
            "games": len(found),
            "not_conceded": len(played),
            "not_conceded_both_450": both_rated(played, 450),
            "not_conceded_both_500": both_rated(played, 500),
            "not_conceded_both_600": both_rated(played, 600),
            "mean_generations": mean([game["generations"] for game in played if isinstance(game["generations"], int)]),
            "mean_points": (
                mean([p["victory_points"] for p in winners if isinstance(p["victory_points"], int)]),
                mean([p["victory_points"] for p in losers if isinstance(p["victory_points"], int)]),
            ),
            "mean_winner_card_points": mean([card_points(p) for p in winners if card_points(p) is not None]),
            "mean_higher_card_points": mean(
                [max(found) for game in played if None not in (found := [card_points(p) for p in game["players"]])]
            ),
        }
    return counts


def results_and_setups(game: Game) -> Game:
    """A Game with only what these tables use: its results and setup Decisions. The whole dataset as
    Python objects is more than a 12 GB laptop holds."""
    kept = {key: value for key, value in game.items() if key not in ("positions", "decisions")}
    kept["decisions"] = [decision for decision in game["decisions"] if decision["kind"] == "setup"]
    return kept


def percent(part: int, whole: int) -> str:
    return f"{100 * part / whole:.1f}%" if whole else "-"


def number(value: float | None, digits: int = 1) -> str:
    return "-" if value is None else f"{value:.{digits}f}"


def report(games: list[Game], least_offered: int) -> str:
    lines = ['The spec\'s table ("What we measured"), from the dataset:']
    counts = spec_counts(games)
    rows = [
        ("All Games", lambda c: f"{c['games']:,}"),
        ("Not conceded", lambda c: f"{c['not_conceded']:,}"),
        ("  both rated 450+", lambda c: f"{c['not_conceded_both_450']:,}"),
        ("  both rated 500+", lambda c: f"{c['not_conceded_both_500']:,}"),
        ("  both rated 600+", lambda c: f"{c['not_conceded_both_600']:,}"),
        ("Mean Generations", lambda c: number(c["mean_generations"])),
        (
            "Mean Victory Points, winner–loser",
            lambda c: f"{number(c['mean_points'][0], 0)}–{number(c['mean_points'][1], 0)}",
        ),
        ("Mean card Victory Points, winner", lambda c: number(c["mean_winner_card_points"])),
        ("  the higher of the two Players", lambda c: number(c["mean_higher_card_points"])),
    ]
    lines.append(f"  {'':36}{'With Prelude':>16}{'Without Prelude':>18}")
    lines += [f"  {label:36}{show(counts['Prelude']):>16}{show(counts['no Prelude']):>18}" for label, show in rows]
    prelude_games = [game for game in games if game["prelude"]]
    lines += ["", f"Setup tables below: {len(prelude_games):,} Games with Prelude."]
    rates = sorted(
        (
            (kept / offered, card, offered)
            for card, (offered, kept) in keep_rates(prelude_games).items()
            if offered >= least_offered
        ),
        reverse=True,
    )
    lines += [
        "",
        f"Starting hand: the 20 most and 20 least kept Project Cards (offered at least {least_offered:,} times):",
    ]
    lines += [f"  {card:36}{rate * 100:>7.1f}% of {offered:>8,}" for rate, card, offered in rates[:20]]
    lines.append("  ...")
    lines += [f"  {card:36}{rate * 100:>7.1f}% of {offered:>8,}" for rate, card, offered in rates[-20:]]
    for title, table in (
        ("Corporations", corporation_table(prelude_games)),
        ("Prelude Cards", prelude_table(prelude_games)),
    ):
        lines += ["", f"{title}: dealt, chosen, chosen of dealt, win rate when chosen:"]
        for card, row in sorted(table.items(), key=lambda item: -item[1]["chosen"]):
            lines.append(
                f"  {card:36}{row['offered']:>9,}{row['chosen']:>9,}{percent(row['chosen'], row['offered']):>9}"
                f"{percent(row['won'], row['chosen']):>9}"
            )
    for title, kind, key in (("Milestones", "milestones", "milestone"), ("Awards", "awards", "award")):
        lines += ["", f"{title}: claimed or funded, mean Generation, win rate of who did:"]
        for name, row in sorted(claims_table(prelude_games, kind, key).items(), key=lambda item: -item[1]["claimed"]):
            lines.append(
                f"  {name:36}{row['claimed']:>9,}{number(row['mean_generation'], 2):>9}{percent(row['won'], row['claimed']):>9}"
            )
    return "\n".join(lines)


def main(arguments: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m ai.recorded_games.tables", description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=DATASET_FOLDER, help="the dataset (default .cache/recorded-games/)")
    parser.add_argument("--least-offered", type=int, default=200, help="for keep rates (default 200)")
    parsed = parser.parse_args(arguments)
    print(report([results_and_setups(game) for game in read_games(parsed.out)], parsed.least_offered))
    return 0


if __name__ == "__main__":
    sys.exit(main())
