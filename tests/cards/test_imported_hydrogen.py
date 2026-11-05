"""#019 Imported Hydrogen (16 MegaCredits, space, Earth and Event Tags): gain 3 plants, or add 3 microbes
or 2 animals to ANOTHER card. Place an Ocean Tile."""

from tests.helpers import (
    OCEAN_AREAS,
    card_resources,
    final_scores,
    hand,
    labels,
    ocean,
    offered,
    pick,
    player,
    resources,
    scenario,
    terraformed_mars,
)


def playing(*played):
    return player(megacredits=16, hand=["imported_hydrogen"], played_cards=played)


def test_without_a_card_for_microbes_or_animals_it_places_its_ocean_and_gains_the_plants():
    game = scenario(playing("mine"), player(played_cards=["tardigrades", "fish"]))

    pick(game, "Play Imported Hydrogen (16 MegaCredits)")
    assert game.decision["kind"] == "area"
    pick(game, area="A2")

    assert resources(game, 0)["plants"] == 3
    assert game.decision["kind"] == "action"


def test_with_cards_for_both_the_player_chooses_among_the_three_once_the_ocean_is_placed():
    game = scenario(playing("tardigrades", "fish"), player())

    pick(game, "Play Imported Hydrogen")
    pick(game, area="A2")

    assert game.decision["kind"] == "effects"
    assert labels(game) == [
        "Gain 3 plants",
        "Add 3 microbes to another card",
        "Add 2 animals to another card",
    ]
    assert game.decision["options"][1]["details"] == {
        "type": "choose_effects",
        "card": "imported_hydrogen",
        "alternative": 1,
    }


def test_choosing_the_plants_gains_them():
    game = scenario(playing("tardigrades", "fish"), player())
    pick(game, "Play Imported Hydrogen")
    pick(game, area="A2")

    pick(game, "Gain 3 plants")

    assert resources(game, 0)["plants"] == 3
    assert card_resources(game, 0) == {"fish": 0, "tardigrades": 0}
    assert game.decision["kind"] == "action"


def test_choosing_the_microbes_adds_them_to_the_only_card_that_holds_them():
    game = scenario(playing("tardigrades", "fish"), player())
    pick(game, "Play Imported Hydrogen")
    pick(game, area="A2")

    pick(game, "Add 3 microbes")

    assert resources(game, 0)["plants"] == 0
    assert card_resources(game, 0) == {"fish": 0, "tardigrades": 3}
    assert game.decision["kind"] == "action"


def test_choosing_the_animals_with_several_cards_for_them_asks_which():
    game = scenario(playing("fish", "birds"), player())
    pick(game, "Play Imported Hydrogen")
    pick(game, area="A2")
    assert labels(game) == ["Gain 3 plants", "Add 2 animals to another card"]

    pick(game, "Add 2 animals")

    assert game.decision["kind"] == "add_to_card"
    assert labels(game) == ["Add 2 animals to Fish", "Add 2 animals to Birds"]
    pick(game, "Add 2 animals to Birds")
    assert card_resources(game, 0) == {"birds": 2, "fish": 0}
    assert game.decision["kind"] == "action"


def test_the_card_the_oceans_placement_bonus_draws_is_seen_before_the_choice():
    game = scenario(playing("fish"), player(), deck=["mine"])

    pick(game, "Play Imported Hydrogen")
    pick(game, area="A4")

    assert game.decision["kind"] == "effects"
    assert hand(game, 0) == ["mine"]


def test_once_all_9_oceans_are_placed_it_can_still_be_played_for_its_choice():
    game = scenario(
        playing("fish"), player(), tiles=[ocean(area) for area in OCEAN_AREAS[:9]]
    )

    pick(game, "Play Imported Hydrogen")

    assert game.decision["kind"] == "effects"
    pick(game, "Gain 3 plants")
    assert resources(game, 0)["plants"] == 3


def test_it_is_offered_without_a_card_for_microbes_or_animals():
    assert offered(scenario(playing(), player()), "Play Imported Hydrogen")


def test_it_scores_no_victory_points():
    played = player(played_cards=["imported_hydrogen"])

    assert (
        final_scores(scenario(played, player(), **terraformed_mars()))[0]["cards"] == 0
    )
