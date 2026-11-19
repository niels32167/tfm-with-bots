"""Position encoding (ticket 12 of phase 2): a position and its Options as numbers, the same from a Player
View with its Decision and from a Recorded Game's record. The tests read like play, through the engine
module's Games and Player Views."""

import math
import random

import pytest
import tm_engine

from ai.controller import handle_for
from ai.encoding import (
    CARD_FIELDS,
    CARD_PRICED_OPTIONS,
    DECISION_KINDS,
    OPTION_FIELDS,
    OPTION_TYPES,
    PAYING_FOR,
    FormatMismatch,
    areas,
    card_number,
    check_format,
    encode,
    format_stamp,
)
from tests.helpers import pick, player, scenario


def new_game(*, seed: int = 1, prelude: bool = True) -> tm_engine.Game:
    return tm_engine.Game(seed=seed, players=2, prelude=prelude)


def test_each_corporation_dealt_is_an_option_named_by_its_card():
    game = new_game()
    handle = handle_for(game, random.Random(1))

    encoded = encode(handle.player_view, handle.decision)

    dealt = [option["details"]["card"] for option in handle.decision["options"]]
    assert [encoded.option(index)["card"] for index in range(len(dealt))] == [card_number(card) for card in dealt]
    assert encoded.option(0)["type"] == encoded.option(1)["type"]


# Random Games until every Decision kind has been encoded, with and without Prelude: the rarest (Vitor's free
# Award, Viral Enhancers, Ecology Experts' card) come up a few times in 400 Games.
MAX_GAMES = 1_000
MAX_PICKS = 10_000
# Every Decision of a kind's first few is encoded; after that, one in this many, to keep the test quick.
ENCODE_ONE_IN = 25
# Lowering a Production is a Decision only when two opponents could lose it, so never in a 2-player Game;
# test_lowering_an_opponents_production_encodes covers it.
RANDOM_PLAY_OPTION_TYPES = set(OPTION_TYPES) - {"lower_production"}


def test_every_decision_kind_encodes_from_random_games_with_nothing_missing():
    seen: dict[str, int] = {}
    option_types: set[str] = set()
    for seed in range(MAX_GAMES):
        game = new_game(seed=seed, prelude=seed % 2 == 0)
        numbers = random.Random(seed)
        for pick_number in range(MAX_PICKS):
            if game.is_over:
                break
            decision = game.decision
            kind = decision["kind"]
            types = {option["details"]["type"] for option in decision["options"]}
            if seen.get(kind, 0) < 3 or not types <= option_types or pick_number % ENCODE_ONE_IN == 0:
                seen[kind] = seen.get(kind, 0) + 1
                encoded = encode(game.player_view(decision["player"]), decision)
                assert encoded.missing_fields() == []
                assert encoded.global_fields()[f"deciding_{kind}"] == 1
                assert len(encoded.options) == len(decision["options"])
                assert len(encoded.areas) == len(areas())
                option_types |= types
                for option, row in zip(decision["options"], encoded.options, strict=True):
                    # An engine view holds the hand and the Tiles, so every Price is known; only Options that
                    # play, keep, buy or give up a card carry one.
                    priced = option["details"]["type"] in CARD_PRICED_OPTIONS
                    assert row[OPTION_FIELDS.index("facts_known")] == float(priced)
                assert all(row[CARD_FIELDS.index("facts_known")] in (0, 1) for row in encoded.cards)
                assert {OPTION_TYPES[int(row[0])] for row in encoded.options} == types
                assert all(math.isfinite(number) for number in encoded.globals)
            game.pick(numbers.randrange(len(decision["options"])))
        if set(seen) == set(DECISION_KINDS) and option_types >= RANDOM_PLAY_OPTION_TYPES:
            break

    assert sorted(set(DECISION_KINDS) - set(seen)) == []
    assert sorted(RANDOM_PLAY_OPTION_TYPES - option_types) == []


def test_lowering_an_opponents_production_encodes():
    # A Target Decision between two opponents' Production, as a 3-player Game offers it, encoded with a
    # 2-player view: the Option names the card, the Player hit and the steps lost.
    three = scenario(player(hand=["heat_trappers"]), player(production={"heat": 2}), player(production={"heat": 3}))
    pick(three, "Play Heat Trappers")
    two = scenario(player(hand=["heat_trappers"]), player(production={"heat": 2}))

    encoded = encode(two.player_view(0), three.decision)

    option = encoded.option(0)
    assert OPTION_TYPES[int(option["type"])] == "lower_production"
    assert option["card"] == card_number("heat_trappers")
    assert option["target"] == 2  # theirs
    assert option["production_heat"] == -2


def test_paying_for_a_prelude_card_encodes_as_paying_for_that_card():
    # Helion may pay Aquifer Turbines' 3 MegaCredits with heat; the engine names the Expense by the card
    # (ticket 14 of phase 2: a recorded Game's Payment once failed to encode).
    game = scenario(
        player(prelude_cards=["aquifer_turbines"], corporation="helion", megacredits=5, heat=3), player(), prelude=True
    )
    pick(game, area="E4")
    assert game.decision["kind"] == "payment"

    encoded = encode(game.player_view(0), game.decision)

    option = encoded.option(0)
    assert PAYING_FOR[int(option["paying_for"]) - 1] == "card"
    assert option["card"] == card_number("aquifer_turbines")


# Positions checked for hidden-card invariance, and the Sampled Positions made for each.
INVARIANCE_GAMES = 30
SAMPLES = 3


def test_the_encoding_never_changes_when_only_hidden_cards_change():
    # A Sampled Position keeps everything the deciding Player can see and deals the rest anew, so the
    # encoding from its Player View must be the same; the other Player's hand and the deck do differ.
    checked = hands_redealt = 0
    for seed in range(INVARIANCE_GAMES):
        game = new_game(seed=seed, prelude=seed % 2 == 0)
        numbers = random.Random(seed)
        for pick_number in range(MAX_PICKS):
            if game.is_over:
                break
            if pick_number % ENCODE_ONE_IN == 0:
                handle = handle_for(game, numbers)
                encoded = encode(handle.player_view, handle.decision)
                for sample_seed in range(SAMPLES):
                    sample = handle.sample(seed=sample_seed)
                    assert encode(sample.player_view(handle.player), sample.decision) == encoded
                    other = 1 - handle.player
                    hands_redealt += (
                        sample.full_view()["players"][other]["hand"] != game.full_view()["players"][other]["hand"]
                    )
                    checked += 1
            game.pick(numbers.randrange(len(game.decision["options"])))

    assert checked > 1_000
    assert hands_redealt > checked / 2


def test_an_encoding_made_with_another_format_is_refused():
    stamp = format_stamp()
    check_format(stamp)

    # An old dataset or model: an earlier version, or the same version number with another layout (a field
    # added without bumping it, or a card catalog changed).
    for old in ({**stamp, "format_version": stamp["format_version"] - 1}, {**stamp, "layout_hash": "0" * 16}, {}):
        with pytest.raises(FormatMismatch, match="encode it again, or retrain"):
            check_format(old)
