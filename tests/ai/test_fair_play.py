"""A Controller is handed a read-only handle, never the Game (ADR 0013): nothing reachable from the
handle is the Game, a copy of it, or a card the deciding Player can't see.

Hidden cards are those the engine knows of that the Player View and Decision don't name: other
Players' hands, Corporations and Prelude Cards being chosen, cards under way in the Draft or being
bought, the deck and the discard pile, and cards that left the Game unseen, such as the Prelude Cards
not kept at setup and the 2 that Valley Trust discards.
"""

import ast
import gc
import json
import random
import re
import types
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import tm_engine

import ai
from ai.controller import Handle, handle_for
from ai.random_bot import RandomBot

CARD_IDS = frozenset(card["id"] for card in tm_engine.card_catalog())
MAX_PICKS = 10_000
QUOTED_WORD = re.compile(r'"([a-z0-9_]+)"')


def reachable(root: object) -> list[object]:
    """Every object reachable from `root` through what it holds: attributes, items, closures and the
    like. Classes and modules are not followed, as they are shared by all code, not handed over."""
    found: dict[int, object] = {}
    waiting = [root]
    while waiting:
        thing = waiting.pop()
        if id(thing) in found:
            continue
        found[id(thing)] = thing
        if not isinstance(thing, (type, types.ModuleType)):
            waiting.extend(gc.get_referents(thing))
    return list(found.values())


def card_ids_in(*data: Any) -> set[str]:
    """The card ids anywhere in the engine module's plain data, as keys or values."""
    return set(QUOTED_WORD.findall(json.dumps(data))) & CARD_IDS


def leaks(handle: object, hidden: Iterable[str]) -> list[str]:
    """What the handle gives away: a Game, or a hidden card."""
    things = reachable(handle)
    games = ["a Game" for thing in things if isinstance(thing, tm_engine.Game)]
    strings = {thing for thing in things if isinstance(thing, str)}
    return games + sorted(strings & set(hidden))


class HiddenCards:
    """Follows a Game and says which cards each Player can't see at each Decision, remembering those
    that left the Game while hidden from them."""

    def __init__(self, players: int) -> None:
        self.hidden_now: list[set[str]] = [set() for _ in range(players)]
        self.gone_unseen: list[set[str]] = [set() for _ in range(players)]

    def update(self, game: tm_engine.Game) -> None:
        known = card_ids_in(game.full_view(), game.to_scenario())
        for player in range(game.players):
            visible = card_ids_in(game.player_view(player), game.decision)
            hidden = known - visible
            self.gone_unseen[player] |= self.hidden_now[player] - known
            self.hidden_now[player] = hidden

    def hidden_from(self, player: int) -> set[str]:
        return self.hidden_now[player] | self.gone_unseen[player]


def test_nothing_reachable_from_the_handle_gives_the_game_or_a_hidden_card():
    games_with_valley_trust_drawing = 0
    for seed in range(7, 13):
        players = 2 if seed % 7 else 3  # 3 Players pass Draft cards in both directions
        game = tm_engine.Game(seed=seed, players=players, draft=True, prelude=True)
        hidden = HiddenCards(players)
        bots = [RandomBot() for _ in range(players)]
        random_numbers = random.Random(seed)
        for _ in range(MAX_PICKS):
            if (decision := game.decision) is None:
                break
            hidden.update(game)
            player = decision["player"]
            handle = handle_for(game, random_numbers)

            assert handle.player == player
            assert leaks(handle, hidden.hidden_from(player)) == [], f"seed {seed}, pick {decision['sequence']}"
            game.pick(bots[player].pick(handle), decision["sequence"])
        assert game.is_over
        boards = game.full_view()["players"]
        games_with_valley_trust_drawing += any(
            board["corporation"] == "valley_trust" and len(board["played_prelude_cards"]) == 3 for board in boards
        )

    assert games_with_valley_trust_drawing > 0, "no Game had Valley Trust draw Prelude Cards; choose other seeds"


def test_the_handle_holds_the_deciding_players_view_and_the_decision():
    game = tm_engine.Game(seed=5, players=2, draft=True, prelude=True)
    decision = game.decision

    handle = handle_for(game, random.Random(1))

    assert handle.player == decision["player"]
    assert handle.player_view == game.player_view(decision["player"])
    assert handle.decision == decision


def test_the_leak_check_finds_a_game_and_a_hidden_card():
    # The check above must be able to fail.
    game = tm_engine.Game(seed=5, players=2, draft=True, prelude=True)
    hidden = HiddenCards(2)
    hidden.update(game)
    player = game.decision["player"]
    opponents_card = min(hidden.hidden_from(player) & card_ids_in(game.player_view(1 - player)))

    assert leaks(Handle(player, {"note": opponents_card}, {}, random.Random(1)), hidden.hidden_from(player)) == [
        opponents_card
    ]
    assert leaks(Handle(0, {}, {"undo": game.copy}, random.Random(1)), set()) == ["a Game"]


def test_no_controller_imports_the_engine():
    # With the engine, a Controller could make Games of its own and find a Match's small seed from the
    # cards dealt to it. Only the seam that builds handles and the Match tool may import it.
    may_import_the_engine = {"controller.py", "match.py"}
    importing = []
    for path in sorted(Path(ai.__file__).parent.rglob("*.py")):
        tree = ast.parse(path.read_text())
        imported = {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
        imported |= {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}
        if "tm_engine" in imported and path.name not in may_import_the_engine:
            importing.append(path.name)

    assert importing == []
