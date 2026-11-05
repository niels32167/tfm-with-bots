"""#026 Eos Chasma National Park (16 MegaCredits, building and plant Tags, 1 Victory Point): requires
-12 °C or warmer. Add 1 animal TO ANY ANIMAL CARD. Gain 3 plants. Increase your MegaCredit Production
2 steps."""

from tests.helpers import (
    card_resources,
    final_scores,
    labels,
    offered,
    pick,
    player,
    production,
    resources,
    scenario,
    terraformed_mars,
)


def hand(*played):
    return player(
        megacredits=16, hand=["eos_chasma_national_park"], played_cards=played
    )


def test_it_requires_minus_12_degrees():
    assert not offered(
        scenario(hand(), player(), temperature=-14), "Play Eos Chasma National Park"
    )
    assert offered(
        scenario(hand(), player(), temperature=-12), "Play Eos Chasma National Park"
    )


def test_it_gains_plants_and_production_and_adds_an_animal_to_the_only_animal_card():
    game = scenario(hand("fish", "tardigrades"), player(), temperature=-12)

    pick(game, "Play Eos Chasma National Park (16 MegaCredits)")

    assert resources(game, 0)["plants"] == 3
    assert production(game, 0)["megacredits"] == 2
    assert card_resources(game, 0) == {"fish": 1, "tardigrades": 0}
    assert game.decision["kind"] == "action"


def test_with_several_animal_cards_the_player_picks_one():
    game = scenario(hand("fish", "birds", "tardigrades"), player(), temperature=-12)

    pick(game, "Play Eos Chasma National Park")

    assert game.decision["kind"] == "add_to_card"
    assert labels(game) == ["Add 1 animal to Fish", "Add 1 animal to Birds"]
    pick(game, type="add_card_resources", to="birds", amount=1, kind="animal")
    assert card_resources(game, 0)["birds"] == 1


def test_without_an_animal_card_it_can_still_be_played_and_the_animal_is_lost():
    game = scenario(hand(), player(played_cards=["fish"]), temperature=-12)

    pick(game, "Play Eos Chasma National Park")

    assert resources(game, 0)["plants"] == 3
    assert card_resources(game, 1) == {"fish": 0}
    assert "Player 1 has no card to add 1 animal to." in game.log


def test_robotic_workforce_copies_its_production_box():
    playing = player(
        megacredits=9,
        hand=["robotic_workforce"],
        played_cards=["eos_chasma_national_park"],
    )
    game = scenario(playing, player())

    pick(game, "Play Robotic Workforce")

    assert production(game, 0)["megacredits"] == 2


def test_it_scores_1_victory_point():
    played = player(played_cards=["eos_chasma_national_park"])

    assert (
        final_scores(scenario(played, player(), **terraformed_mars()))[0]["cards"] == 1
    )
