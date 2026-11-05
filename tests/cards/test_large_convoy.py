"""#143 Large Convoy (36 MegaCredits, space, Earth and Event Tags, 2 Victory Points): place an Ocean Tile
and draw 2 cards. Gain 5 plants or add 4 animals to ANOTHER card."""

from tests.helpers import (
    card_resources,
    final_scores,
    hand,
    labels,
    pick,
    player,
    resources,
    scenario,
    terraformed_mars,
)


def playing(*played):
    return player(megacredits=36, hand=["large_convoy"], played_cards=played)


def test_without_an_animal_card_it_places_its_ocean_draws_2_cards_and_gains_the_plants():
    game = scenario(playing(), player(played_cards=["fish"]), deck=["mine", "trees"])

    pick(game, "Play Large Convoy (36 MegaCredits)")
    pick(game, area="A2")

    assert sorted(hand(game, 0)) == ["mine", "trees"]
    assert resources(game, 0)["plants"] == 5
    assert card_resources(game, 1) == {"fish": 0}
    assert game.decision["kind"] == "action"


def test_with_an_animal_card_the_player_chooses_once_the_ocean_is_placed():
    game = scenario(playing("tardigrades", "fish"), player(), deck=["mine", "trees"])

    pick(game, "Play Large Convoy")
    pick(game, area="A2")

    assert game.decision["kind"] == "effects"
    assert labels(game) == ["Gain 5 plants", "Add 4 animals to another card"]
    pick(game, "Add 4 animals")
    assert card_resources(game, 0) == {"fish": 4, "tardigrades": 0}
    assert resources(game, 0)["plants"] == 0


def test_a_player_may_gain_the_plants_with_an_animal_card_in_play():
    game = scenario(playing("fish"), player(), deck=["mine", "trees"])
    pick(game, "Play Large Convoy")
    pick(game, area="A2")

    pick(game, "Gain 5 plants")

    assert resources(game, 0)["plants"] == 5
    assert card_resources(game, 0) == {"fish": 0}


def test_it_scores_2_victory_points():
    played = player(played_cards=["large_convoy"])

    assert (
        final_scores(scenario(played, player(), **terraformed_mars()))[0]["cards"] == 2
    )
