"""Compares a Controller's setup choices with Players' in Recorded Games (ticket 11): how often each
Corporation is chosen, and each Prelude Card kept, when it is dealt.

    uv run python -m tools.setup_choices
    uv run python -m tools.setup_choices --controller card_economy --setups 4000 --min-rating 400

The Controller answers every setup Decision of both Players in --setups new 2-player Prelude Games with
the Draft, as in a Match, and stops when the first Generation's Action phase begins. Players' rates come
from the dataset's setup records (ai.recorded_games.tables), in Prelude Games not conceded whose lower
rating is at least --min-rating. Rows are sorted by the size of the difference, largest first.
"""

import argparse
import random
import sys
from collections.abc import Iterable, Sequence
from typing import Any

import tm_engine

from ai.controller import card_catalog, handle_for
from ai.controllers import REGISTERED, make_controller
from ai.recorded_games.dataset import read_games
from ai.recorded_games.tables import corporation_table, prelude_table, results_and_setups

# How setup Decisions name what they choose: the kind of Decision and the kind of Option.
CHOOSING = {"corporation": "choose_corporation", "prelude_cards": "keep_prelude_card"}

# A guard on the picks of one setup.
MOST_PICKS = 500

type Table = dict[str, dict[str, int]]


def controller_choices(name: str, setups: int, first_seed: int = 0) -> tuple[Table, Table]:
    """How often the Controller chose each Corporation and kept each Prelude Card it was dealt, as
    tables shaped like ai.recorded_games.tables': "offered" and "chosen" by card."""
    corporations: Table = {}
    preludes: Table = {}
    for seed in range(first_seed, first_seed + setups):
        game = tm_engine.Game(seed=seed, players=2, draft=True, prelude=True)
        answering = [make_controller(name) for _ in range(2)]
        random_sources = [random.Random(f"{seed}/{player}") for player in range(2)]
        dealt: dict[tuple[str, int], list[str]] = {}
        chosen: dict[tuple[str, int], list[str]] = {}
        for _ in range(MOST_PICKS):
            decision = game.decision
            if decision is None or game.player_view(0)["phase"] == "action":
                break
            player = decision["player"]
            index = answering[player].pick(handle_for(game, random_sources[player]))
            if decision["kind"] in CHOOSING:
                cards = [
                    o["details"]["card"]
                    for o in decision["options"]
                    if o["details"]["type"] == CHOOSING[decision["kind"]]
                ]
                key = (decision["kind"], player)
                dealt.setdefault(key, cards)
                chosen.setdefault(key, []).append(decision["options"][index]["details"].get("card"))
            game.pick(index)
        for key, cards in dealt.items():
            table = corporations if key[0] == "corporation" else preludes
            picked = set(chosen[key])
            for card in cards:
                row = table.setdefault(card, {"offered": 0, "chosen": 0})
                row["offered"] += 1
                row["chosen"] += card in picked
    return corporations, preludes


def players_games(min_rating: int) -> Iterable[dict[str, Any]]:
    """The suitable Games, each slimmed to its results and setup: the whole dataset as Python objects is
    more than the laptop holds."""
    for game in read_games():
        ratings = [player["rating"] or 0 for player in game["players"]]
        if game["prelude"] and not game["conceded"] and min(ratings) >= min_rating:
            yield results_and_setups(game)


def comparison(title: str, players: Table, controller: Table, label: str) -> str:
    rows = []
    for card in set(players) | set(controller):
        human = players.get(card, {"offered": 0, "chosen": 0})
        bot = controller.get(card, {"offered": 0, "chosen": 0})
        if not human["offered"] or not bot["offered"]:
            continue
        human_rate = human["chosen"] / human["offered"]
        bot_rate = bot["chosen"] / bot["offered"]
        rows.append((abs(bot_rate - human_rate), card, human_rate, human["offered"], bot_rate, bot["offered"]))
    rows.sort(reverse=True)
    lines = [title, f"{'':32}{'Players':>10}{'dealt':>9}{label:>16}{'dealt':>8}{'difference':>12}"]
    for _, card, human_rate, human_offered, bot_rate, bot_offered in rows:
        name = card_catalog()[card]["name"]
        lines.append(
            f"{name:32}{human_rate:>10.0%}{human_offered:>9,}{bot_rate:>16.0%}{bot_offered:>8,}"
            f"{(bot_rate - human_rate) * 100:>+11.0f}"
        )
    return "\n".join(lines)


def main(arguments: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--controller", default="card_economy", choices=sorted(REGISTERED))
    parser.add_argument("--setups", type=int, default=4000, help="Games whose setup the Controller plays (4000)")
    parser.add_argument("--min-rating", type=int, default=0, help="the lower Player's least rating (0)")
    options = parser.parse_args(arguments)

    corporations, preludes = controller_choices(options.controller, options.setups)
    games = list(players_games(options.min_rating))
    label = REGISTERED[options.controller].label.removesuffix(" Bot")
    print(f"{len(games):,} Prelude Games from the dataset (lower rating {options.min_rating}+); the {label} Bot")
    print(f"answering both Players' setup in {options.setups:,} Games. Rates are chosen or kept when dealt.\n")
    print(
        comparison("Corporations, chosen when dealt (2 of them dealt):", corporation_table(games), corporations, label)
    )
    print()
    print(comparison("Prelude Cards, kept when dealt (4 dealt, 2 kept):", prelude_table(games), preludes, label))
    return 0


if __name__ == "__main__":
    sys.exit(main())
