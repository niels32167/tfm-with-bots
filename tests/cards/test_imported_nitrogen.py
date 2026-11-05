"""#163 Imported Nitrogen (23 MegaCredits, space, Earth and Event Tags): raise your Terraform Rating 1
step and gain 4 plants. Add 3 microbes to ANOTHER card and 2 animals to ANOTHER card."""

from tests.helpers import (
    card_resources,
    final_scores,
    labels,
    pick,
    player,
    player_board,
    resources,
    scenario,
    terraformed_mars,
)


def hand(*played):
    return player(megacredits=23, hand=["imported_nitrogen"], played_cards=played)


def test_it_raises_terraform_rating_gains_plants_and_adds_to_the_only_cards_without_a_decision():
    game = scenario(hand("tardigrades", "fish"), player())

    pick(game, "Play Imported Nitrogen (23 MegaCredits)")

    assert player_board(game, 0)["terraform_rating"] == 21
    assert resources(game, 0)["plants"] == 4
    assert card_resources(game, 0) == {"fish": 2, "tardigrades": 3}
    assert game.decision["kind"] == "action"


def test_the_player_picks_the_card_for_the_microbes_then_for_the_animals():
    game = scenario(hand("tardigrades", "ants", "fish", "birds"), player())

    pick(game, "Play Imported Nitrogen")

    assert labels(game) == ["Add 3 microbes to Ants", "Add 3 microbes to Tardigrades"]
    pick(game, "Add 3 microbes to Ants")
    assert labels(game) == ["Add 2 animals to Fish", "Add 2 animals to Birds"]
    pick(game, "Add 2 animals to Birds")
    assert card_resources(game, 0) == {
        "ants": 3,
        "birds": 2,
        "fish": 0,
        "tardigrades": 0,
    }
    assert game.decision["kind"] == "action"


def test_without_a_card_for_them_the_card_resources_are_lost_and_the_rest_is_carried_out():
    game = scenario(hand("fish"), player())

    pick(game, "Play Imported Nitrogen")

    assert "Player 1 has no card to add 3 microbes to." in game.log
    assert card_resources(game, 0) == {"fish": 2}
    assert resources(game, 0)["plants"] == 4


def test_it_gives_no_card_resources_to_another_players_cards():
    game = scenario(hand(), player(played_cards=["tardigrades", "fish"]))

    pick(game, "Play Imported Nitrogen")

    assert card_resources(game, 1) == {"fish": 0, "tardigrades": 0}


def test_it_scores_no_victory_points():
    played = player(played_cards=["imported_nitrogen"])

    assert (
        final_scores(scenario(played, player(), **terraformed_mars()))[0]["cards"] == 0
    )
