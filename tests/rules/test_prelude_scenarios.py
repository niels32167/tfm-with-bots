"""Scenarios with Prelude. A Scenario with `prelude` on may name the Prelude box's Project Cards and
Prelude Cards: those a Player has played, and those they kept and have still to play, with which the
Scenario starts at the step where Players play them, before the Action phase. A Prelude Card that can't
be played when its Player picks it is discarded instead, and they gain 15 MegaCredits."""

import pytest
import tm_engine

from tests.helpers import (
    hand,
    labels,
    options,
    pick,
    player,
    player_board,
    prelude_cards,
    production,
    resources,
    scenario,
)


def test_a_scenario_starts_where_players_play_the_prelude_cards_they_kept():
    game = scenario(player(prelude_cards=["donation", "loan"]), player(), prelude=True)

    assert game.full_view()["phase"] == "prelude_cards"
    assert game.decision["player"] == 0
    assert game.decision["kind"] == "play_prelude_card"
    assert labels(game) == ["Play Donation", "Play Loan"]
    assert options(game)[0]["details"] == {"type": "play_prelude_card", "card": "donation", "playable": True}


def test_playing_a_prelude_card_carries_out_its_effects_and_the_last_one_follows_without_a_decision():
    game = scenario(player(prelude_cards=["donation", "loan"]), player(), prelude=True)

    pick(game, "Play Loan")

    assert resources(game, 0)["megacredits"] == 42 + 30 + 21
    assert production(game, 0)["megacredits"] == -2
    assert player_board(game, 0)["played_prelude_cards"] == ["donation", "loan"]
    assert prelude_cards(game, 0) == {"dealt": [], "kept": []}
    assert game.full_view()["phase"] == "action"
    assert game.decision == {**game.decision, "player": 0, "kind": "action"}


def test_players_with_no_prelude_cards_left_are_passed_over():
    game = scenario(player(), player(prelude_cards=["donation"]), player(), prelude=True)

    assert resources(game, 1)["megacredits"] == 42 + 21
    assert game.full_view()["phase"] == "action"
    assert game.decision["player"] == 0


def test_a_prelude_card_that_cant_be_played_is_discarded_for_15_megacredits():
    game = scenario(player(prelude_cards=["loan", "donation"], production={"megacredits": -4}), player(), prelude=True)

    assert labels(game) == ["Play Donation", "Discard Loan for 15 MegaCredits (it can't be played)"]
    assert options(game)[1]["details"] == {"type": "play_prelude_card", "card": "loan", "playable": False}
    pick(game, "Discard Loan")

    assert "Player 1 can't play Loan, so they discard it and gain 15 MegaCredits." in game.log
    assert resources(game, 0)["megacredits"] == 42 + 15 + 21
    assert production(game, 0)["megacredits"] == -4
    assert player_board(game, 0)["played_prelude_cards"] == ["donation"]


def test_the_last_prelude_card_is_discarded_without_a_decision_if_it_cant_be_played():
    game = scenario(player(prelude_cards=["donation", "loan"], production={"megacredits": -4}), player(), prelude=True)

    pick(game, "Play Donation")

    assert resources(game, 0)["megacredits"] == 42 + 21 + 15
    assert player_board(game, 0)["played_prelude_cards"] == ["donation"]


def test_the_tags_of_played_prelude_cards_count():
    game = scenario(player(played_prelude_cards=["dome_farming"]), player(), prelude=True)

    tags = player_board(game, 0)["tags"]
    assert (tags["building"], tags["plant"]) == (1, 1)
    assert player_board(game, 0)["played_prelude_cards"] == ["dome_farming"]
    assert player_board(game, 0)["played_cards"] == []


def test_preludes_project_cards_may_be_in_a_hand_with_prelude_but_are_not_offered_until_implemented():
    game = scenario(player(hand=["house_printing"], megacredits=50), player(), prelude=True)

    assert hand(game, 0) == ["house_printing"]
    assert not [label for label in labels(game) if "House Printing" in label]


@pytest.mark.parametrize(
    "fields",
    [
        {"prelude_cards": ["donation"]},
        {"played_prelude_cards": ["donation"]},
        {"hand": ["house_printing"]},
    ],
)
def test_without_prelude_a_scenario_cannot_name_the_prelude_boxs_cards(fields):
    with pytest.raises(ValueError, match="Prelude"):
        scenario(player(**fields), player())


@pytest.mark.parametrize(
    ("fields", "reason"),
    [
        ({"prelude_cards": ["mine"]}, "no Prelude Card 'mine'"),
        ({"played_prelude_cards": ["house_printing"]}, "no Prelude Card 'house_printing'"),
        ({"prelude_cards": ["research_network"]}, "not implemented"),
        ({"prelude_cards": ["donation", "loan", "mohole"]}, "at most 2"),
        ({"prelude_cards": ["donation"], "played_prelude_cards": ["donation"]}, "only one place"),
    ],
)
def test_a_scenario_refuses_prelude_cards_the_rules_never_allow(fields, reason):
    with pytest.raises(ValueError, match=reason):
        scenario(player(**fields), player(), prelude=True)


def test_a_scenario_with_prelude_cards_still_to_play_cannot_be_in_the_middle_of_a_turn():
    with pytest.raises(ValueError, match="Prelude Cards"):
        scenario(player(prelude_cards=["donation"]), player(), prelude=True, actions_this_turn=1)


def test_a_game_playing_its_prelude_cards_described_as_a_scenario_starts_there_again():
    game = scenario(
        player(prelude_cards=["donation", "loan"]), player(prelude_cards=["mohole", "supplier"]), prelude=True
    )
    pick(game, "Play Loan")

    described = game.to_scenario()

    assert described["prelude"] is True
    assert described["players"][0]["played_prelude_cards"] == ["donation", "loan"]
    assert described["players"][1]["prelude_cards"] == ["mohole", "supplier"]
    again = tm_engine.Game.from_scenario(described)
    assert again.full_view()["players"] == game.full_view()["players"]
    assert again.decision["options"] == game.decision["options"]
