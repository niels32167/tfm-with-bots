"""#035 Ants (9 MegaCredits, microbe Tag, requires 4 % Oxygen): Action: remove 1 microbe from any card
to add 1 to this card. 1 Victory Point per 2 microbes on this card."""

from tests.helpers import (
    card_resources,
    final_scores,
    labels,
    offered,
    pick,
    player,
    scenario,
    terraformed_mars,
)


def test_ants_requires_4_percent_oxygen():
    hand = player(megacredits=9, hand=["ants"])

    assert not offered(scenario(hand, player(), oxygen=3), "Play Ants")
    assert offered(scenario(hand, player(), oxygen=4), "Play Ants")


def test_with_one_card_to_take_from_the_action_moves_the_microbe_without_a_decision():
    game = scenario(
        player(played_cards=["ants"]),
        player(played_cards=["tardigrades"], card_resources={"tardigrades": 2}),
    )

    pick(game, "Use the action of Ants")

    assert card_resources(game, 0) == {"ants": 1}
    assert card_resources(game, 1) == {"tardigrades": 1}
    assert "Player 1 moves 1 microbe from Player 2's Tardigrades to Ants." in game.log
    assert game.decision["kind"] == "action"


def test_the_player_picks_among_the_opponents_cards_with_microbes_and_their_own_are_left_out():
    game = scenario(
        player(
            played_cards=["ants", "regolith_eaters"],
            card_resources={"regolith_eaters": 5},
        ),
        player(
            played_cards=["tardigrades", "physics_complex"],
            card_resources={"tardigrades": 1, "physics_complex": 1},
        ),
        player(
            played_cards=["decomposers", "ghg_producing_bacteria"],
            card_resources={"decomposers": 3},
        ),
    )

    pick(game, "Use the action of Ants")

    assert game.decision["kind"] == "target"
    assert labels(game) == [
        "Remove 1 microbe from Player 2's Tardigrades",
        "Remove 1 microbe from Player 3's Decomposers",
    ]
    pick(
        game,
        type="move_card_resource",
        card="ants",
        player=2,
        **{"from": "decomposers"},
        kind="microbe",
    )
    assert card_resources(game, 0) == {"ants": 1, "regolith_eaters": 5}
    assert card_resources(game, 2) == {"decomposers": 2, "ghg_producing_bacteria": 0}
    assert game.decision["kind"] == "action"


def test_with_no_opponent_to_take_from_the_player_may_move_microbes_from_their_own_cards():
    game = scenario(
        player(
            played_cards=["ants", "regolith_eaters", "tardigrades"],
            card_resources={"ants": 4, "regolith_eaters": 2, "tardigrades": 1},
        ),
        player(played_cards=["physics_complex"], card_resources={"physics_complex": 1}),
    )

    pick(game, "Use the action of Ants")

    assert labels(game) == [
        "Remove 1 microbe from your own Regolith Eaters",
        "Remove 1 microbe from your own Ants",
        "Remove 1 microbe from your own Tardigrades",
    ]
    pick(game, "your own Regolith Eaters")
    assert card_resources(game, 0) == {
        "ants": 5,
        "regolith_eaters": 1,
        "tardigrades": 1,
    }
    assert (
        "Player 1 moves 1 microbe from their own Regolith Eaters to Ants." in game.log
    )


def test_with_microbes_only_on_ants_itself_the_action_moves_one_back_onto_it():
    game = scenario(
        player(played_cards=["ants", "tardigrades"], card_resources={"ants": 3}),
        player(played_cards=["physics_complex"], card_resources={"physics_complex": 2}),
    )

    pick(game, "Use the action of Ants")

    assert card_resources(game, 0) == {"ants": 3, "tardigrades": 0}
    assert "Player 1 moves 1 microbe from their own Ants to Ants." in game.log
    assert game.decision["kind"] == "action"


def test_the_action_is_not_offered_without_a_microbe_on_any_card():
    game = scenario(
        player(played_cards=["ants", "tardigrades"]),
        player(
            played_cards=["regolith_eaters", "physics_complex"],
            card_resources={"physics_complex": 2},
        ),
    )

    assert not offered(game, "Use the action of Ants")


def test_the_action_is_not_offered_again_this_generation():
    game = scenario(
        player(played_cards=["ants"]),
        player(played_cards=["tardigrades"], card_resources={"tardigrades": 5}),
    )

    pick(game, "Use the action of Ants")

    assert not offered(game, "Use the action of Ants")


def test_ants_scores_1_victory_point_per_2_microbes():
    for microbes, points in ((1, 0), (2, 1), (5, 2)):
        holding = player(played_cards=["ants"], card_resources={"ants": microbes})

        assert (
            final_scores(scenario(holding, player(), **terraformed_mars()))[0]["cards"]
            == points
        )
