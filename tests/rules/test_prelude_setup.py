"""The Prelude setting and what it adds to setup (ADR 0011). With Prelude, each Player is also dealt 4 Prelude
Cards at setup and keeps 2, chosen with their Corporation and cards to buy and hidden until every
Player is done. Once every Corporation is revealed and every card paid for, each Player in player order
plays both their Prelude Cards, in the order they choose, before the first Action phase. Each card's own
effects are in tests/cards/test_<id>.py."""

import json

import pytest
import tm_engine

from tests.helpers import (
    CARD_NAMES,
    CARDS,
    CORPORATIONS,
    PRELUDE_CORPORATIONS,
    PROJECT_CARDS,
    everything_about,
    labels,
    options,
    pick,
    place_tiles_anywhere,
    play_randomly,
    player,
    player_board,
    prelude_cards,
    scenario,
    skip_buying,
)

PRELUDE_CARDS_DEALT = 4


@pytest.mark.parametrize("players", [2, 3, 4, 5])
def test_with_prelude_each_player_is_dealt_4_prelude_cards_none_of_them_dealt_twice(players):
    view = tm_engine.Game(seed=7, players=players, prelude=True).full_view()

    dealt = [board["prelude_cards"]["dealt"] for board in view["players"]]
    assert all(len(cards) == PRELUDE_CARDS_DEALT for cards in dealt)
    everyone_was_dealt = [card for cards in dealt for card in cards]
    assert len(set(everyone_was_dealt)) == PRELUDE_CARDS_DEALT * players
    assert all(CARDS[card]["type"] == "prelude" for card in everyone_was_dealt)


def test_the_prelude_cards_dealt_come_from_the_seed():
    def dealt(seed):
        game = tm_engine.Game(seed=seed, prelude=True)
        return [board["prelude_cards"]["dealt"] for board in game.full_view()["players"]]

    assert dealt(7) == dealt(7)
    assert any(dealt(7) != dealt(seed) for seed in range(8, 18))


def test_without_prelude_nobody_is_dealt_prelude_cards():
    view = tm_engine.Game(seed=7, players=3).full_view()

    assert all(board["prelude_cards"] is None for board in view["players"])
    assert all(board["played_prelude_cards"] == [] for board in view["players"])


def test_after_choosing_a_corporation_a_player_keeps_2_of_their_prelude_cards_then_buys():
    game = tm_engine.Game(seed=7, prelude=True)
    first = game.decision["player"]
    game.pick(0)  # their Corporation
    dealt = prelude_cards(game, first)["dealt"]

    assert game.decision["kind"] == "prelude_cards"
    assert labels(game) == [f"Keep {CARD_NAMES[card]}" for card in dealt]
    pick(game, type="keep_prelude_card", card=dealt[2])

    assert game.decision["player"] == first
    assert [option["details"]["card"] for option in options(game)] == [dealt[0], dealt[1], dealt[3]]
    pick(game, type="keep_prelude_card", card=dealt[0])

    assert game.decision == {**game.decision, "player": first, "kind": "buy_cards"}
    assert prelude_cards(game, first) == {"dealt": dealt, "kept": [dealt[0], dealt[2]]}


def test_without_corporations_a_player_keeps_their_prelude_cards_first():
    game = tm_engine.Game(seed=7, prelude=True, corporations=False)

    assert game.decision["kind"] == "prelude_cards"
    assert len(options(game)) == PRELUDE_CARDS_DEALT


def test_the_prelude_cards_dealt_and_kept_show_only_in_their_own_view_until_played():
    game = tm_engine.Game(seed=7, players=3, prelude=True)
    first = game.decision["player"]
    game.pick(0)
    game.pick(0)
    game.pick(0)

    for viewer in range(3):
        view = game.player_view(viewer)
        for index, board in enumerate(view["players"]):
            assert (board["prelude_cards"] is not None) == (index == viewer)
    assert prelude_cards(game, first)["kept"]

    skip_buying(game)

    for viewer in range(3):
        others = [board for index, board in enumerate(game.player_view(viewer)["players"]) if index != viewer]
        assert all(board["prelude_cards"] is None for board in others)
    every_view_text = json.dumps([game.player_view(viewer) for viewer in range(3) if viewer != first])
    kept_by_first_still_to_play = prelude_cards(game, first)["kept"]
    assert not any(card in every_view_text for card in kept_by_first_still_to_play)


def test_once_every_player_is_done_buying_the_prelude_cards_not_kept_go_back_in_the_box():
    game = tm_engine.Game(seed=7, prelude=True)
    skip_buying(game)

    view = game.full_view()
    assert view["phase"] == "prelude_cards"
    assert all(board["prelude_cards"]["dealt"] == [] for board in view["players"])
    assert all(len(board["prelude_cards"]["kept"]) == 2 for board in view["players"])


def test_each_player_in_player_order_plays_both_prelude_cards_in_the_order_they_choose_then_generation_1_begins():
    game = tm_engine.Game(seed=7, players=3, prelude=True)
    skip_buying(game)
    first = game.full_view()["first_player"]
    order = [(first + offset) % 3 for offset in range(3)]

    played_in_order = []
    for deciding in order:
        assert game.decision["player"] == deciding
        assert game.decision["kind"] == "play_prelude_card"
        kept = prelude_cards(game, deciding)["kept"]
        assert [option["details"]["card"] for option in options(game)] == kept
        pick(game, type="play_prelude_card", card=kept[1])
        # The last one is played without a Decision, once the first is done.
        place_tiles_anywhere(game)
        assert player_board(game, deciding)["played_prelude_cards"] == kept
        played_in_order += [kept[1], kept[0]]

    view = game.full_view()
    assert view["phase"] == "action"
    assert view["generation"] == 1
    assert game.decision == {**game.decision, "player": first, "kind": "action"}
    players_in_order = [deciding for deciding in order for _ in range(2)]
    assert [line for line in game.log if line.startswith("Player") and " plays " in line] == [
        f"Player {deciding + 1} plays {CARD_NAMES[card]}."
        for deciding, card in zip(players_in_order, played_in_order, strict=True)
    ]


PRELUDE_PROJECT_CARDS = [
    card["id"] for card in tm_engine.card_catalog()
    if card["expansion"] == "prelude" and card["type"] in ("automated", "active", "event")
]


@pytest.mark.parametrize("prelude", [True, False])
def test_the_deck_has_preludes_project_cards_only_with_prelude(prelude):
    view = tm_engine.Game(seed=7, players=2, prelude=prelude).full_view()

    in_the_game = set(view["deck"]) | {card for board in view["players"] for card in board["buying"]["dealt"]}
    assert len(in_the_game) == len(PROJECT_CARDS) + (len(PRELUDE_PROJECT_CARDS) if prelude else 0)
    assert (set(PRELUDE_PROJECT_CARDS) <= in_the_game) == prelude
    assert set(PROJECT_CARDS) <= in_the_game


@pytest.mark.parametrize("prelude", [True, False])
def test_preludes_corporations_are_dealt_only_with_prelude(prelude):
    dealt = set()
    for seed in range(40):
        view = tm_engine.Game(seed=seed, players=5, prelude=prelude).full_view()
        dealt |= {card for board in view["players"] for card in board["choosing_corporation"]["dealt"]}

    assert PRELUDE_CORPORATIONS == ["cheung_shing_mars", "point_luna", "robinson_industries", "valley_trust", "vitor"]
    assert (set(PRELUDE_CORPORATIONS) <= dealt) == prelude
    assert set(CORPORATIONS) <= dealt
    assert dealt <= set(CORPORATIONS) | set(PRELUDE_CORPORATIONS)


def test_a_replay_names_prelude_only_when_it_is_on():
    with_prelude = tm_engine.Game(seed=7, prelude=True).replay["start"]["settings"]
    without = tm_engine.Game(seed=7).replay["start"]["settings"]

    assert with_prelude["prelude"] is True
    assert "prelude" not in without


@pytest.mark.parametrize("players", [2, 5])
def test_a_whole_random_game_with_prelude_loads_from_its_replay(players):
    game = tm_engine.Game(seed=11, players=players, prelude=True)
    play_randomly(game, seed=3)

    loaded = tm_engine.Game.from_replay(json.loads(json.dumps(game.replay)))

    assert loaded.is_over
    assert everything_about(loaded) == everything_about(game)
    assert all(len(board["played_prelude_cards"]) + discarded(game, index) == 2
               for index, board in enumerate(game.full_view()["players"]))


def discarded(game, player):
    """How many Prelude Cards `player` discarded for 15 MegaCredits, as the game log says."""
    return sum(line.startswith(f"Player {player + 1} can't play") for line in game.log)


def test_a_replay_saved_before_prelude_existed_plays_without_it():
    settings = {"players": 2, "seed": 7, "draft": True, "corporations": True}

    game = tm_engine.Game.from_replay({"start": {"settings": settings}, "picks": []})

    assert everything_about(game) == everything_about(tm_engine.Game(seed=7))
    assert all(board["prelude_cards"] is None for board in game.full_view()["players"])


def test_a_corporations_first_action_comes_after_the_prelude_cards():
    game = scenario(
        player(corporation="inventrix", first_action_due=True, prelude_cards=["donation", "loan"]),
        player(),
        prelude=True,
    )

    assert game.decision["kind"] == "play_prelude_card"
    pick(game, "Play Donation")

    assert labels(game) == ["First action of Inventrix: draw 3 cards", "Pass"]


def test_a_game_that_asks_for_the_last_prelude_card_waits_on_it_as_a_decision_of_its_own():
    game = tm_engine.Game(seed=7, prelude=True, ask_last_prelude_card=True)
    skip_buying(game)
    first = game.decision["player"]
    kept = prelude_cards(game, first)["kept"]

    pick(game, type="play_prelude_card", card=kept[1])
    place_tiles_anywhere(game)

    assert (game.decision["player"], game.decision["kind"]) == (first, "play_prelude_card")
    assert [option["details"]["card"] for option in options(game)] == [kept[0]]
    assert player_board(game, first)["played_prelude_cards"] == [kept[1]]

    pick(game, type="play_prelude_card", card=kept[0])
    place_tiles_anywhere(game)

    assert player_board(game, first)["played_prelude_cards"] == kept
    assert game.decision["player"] != first


def test_a_replay_names_asking_for_the_last_prelude_card_only_when_it_is_on_and_plays_the_same_with_it():
    game = tm_engine.Game(seed=11, prelude=True, ask_last_prelude_card=True)
    play_randomly(game, seed=3)
    loaded = tm_engine.Game.from_replay(json.loads(json.dumps(game.replay)))

    assert game.replay["start"]["settings"]["ask_last_prelude_card"] is True
    assert everything_about(loaded) == everything_about(game)
    assert "ask_last_prelude_card" not in tm_engine.Game(seed=11, prelude=True).replay["start"]["settings"]


def test_a_scenario_may_ask_for_the_last_prelude_card_and_a_position_waiting_on_it_is_one():
    game = scenario(
        player(prelude_cards=["donation", "loan"]), player(), prelude=True, ask_last_prelude_card=True
    )
    pick(game, "Play Donation")
    again = tm_engine.Game.from_scenario(game.to_scenario())

    assert labels(game) == ["Play Loan"]
    assert labels(again) == ["Play Loan"]
    assert "ask_last_prelude_card" not in scenario(player(), player(), prelude=True).to_scenario()


def test_a_sampled_position_asks_for_the_last_prelude_card_if_the_game_does():
    game = scenario(
        player(prelude_cards=["donation", "loan"]), player(), prelude=True, ask_last_prelude_card=True
    )
    sample = game.sampler(0).sample(seed=1)
    pick(sample, "Play Donation")

    assert labels(sample) == ["Play Loan"]
