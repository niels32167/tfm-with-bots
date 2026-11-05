"""#190 Local Heat Trapping (1 MegaCredit, Event Tag): spend 5 heat to gain either 4 plants, or to add 2
animals to ANOTHER card."""

from tests.helpers import (
    card_resources,
    final_scores,
    labels,
    offered,
    pick,
    player,
    resources,
    scenario,
    terraformed_mars,
)


def playing(heat=5, *played):
    return player(
        megacredits=1, heat=heat, hand=["local_heat_trapping"], played_cards=played
    )


def test_it_needs_5_heat_to_spend():
    assert not offered(scenario(playing(heat=4), player()), "Play Local Heat Trapping")
    assert offered(scenario(playing(heat=5), player()), "Play Local Heat Trapping")


def test_without_an_animal_card_it_spends_the_heat_and_gains_the_plants():
    game = scenario(playing(7), player(played_cards=["fish"]))

    pick(game, "Play Local Heat Trapping (1 MegaCredit)")

    assert resources(game, 0)["heat"] == 2
    assert resources(game, 0)["plants"] == 4
    assert game.decision["kind"] == "action"


def test_with_an_animal_card_the_player_chooses():
    game = scenario(playing(5, "fish"), player())

    pick(game, "Play Local Heat Trapping")

    assert resources(game, 0)["heat"] == 0
    assert game.decision["kind"] == "effects"
    assert labels(game) == ["Gain 4 plants", "Add 2 animals to another card"]
    pick(game, "Add 2 animals")
    assert card_resources(game, 0) == {"fish": 2}
    assert resources(game, 0)["plants"] == 0
    assert game.decision["kind"] == "action"


def test_a_player_may_gain_the_plants_with_an_animal_card_in_play():
    game = scenario(playing(5, "fish"), player())
    pick(game, "Play Local Heat Trapping")

    pick(game, "Gain 4 plants")

    assert resources(game, 0)["plants"] == 4
    assert card_resources(game, 0) == {"fish": 0}


def test_it_scores_no_victory_points():
    played = player(played_cards=["local_heat_trapping"])

    assert (
        final_scores(scenario(played, player(), **terraformed_mars()))[0]["cards"] == 0
    )
