"""#075 Towing a Comet (23 MegaCredits, Event and space Tags): gain 2 plants. Raise Oxygen 1 step
and place an Ocean Tile."""

from tests.helpers import (
    OCEAN_AREAS,
    area,
    final_scores,
    ocean,
    pick,
    player,
    player_board,
    resources,
    scenario,
    terraformed_mars,
)


def test_towing_a_comet_gains_2_plants_raises_oxygen_and_places_an_ocean():
    game = scenario(player(megacredits=23, hand=["towing_a_comet"]), player())

    pick(game, "Play Towing a Comet (23 MegaCredits)")
    assert resources(game, 0)["plants"] == 2
    assert game.player_view(0)["oxygen"] == 1
    pick(game, area="E4")

    assert area(game, "E4")["tile"]["type"] == "ocean"
    assert player_board(game, 0)["terraform_rating"] == 22
    assert resources(game, 0)["megacredits"] == 0
    assert game.decision["kind"] == "action"


def test_towing_a_comet_reaching_8_percent_oxygen_and_0_degrees_places_the_bonus_ocean_and_its_own():
    game = scenario(player(hand=["towing_a_comet"]), player(), oxygen=7, temperature=-2)

    pick(game, "Play Towing a Comet")
    assert game.player_view(0)["temperature"] == 0
    pick(game, area="A2")  # the Ocean at 0 °C
    assert game.decision["kind"] == "area"
    pick(game, area="A4")  # the card's own

    assert game.player_view(0)["oceans"] == 2
    assert player_board(game, 0)["terraform_rating"] == 24
    assert game.decision["kind"] == "action"


def test_once_9_oceans_are_placed_towing_a_comet_still_gains_plants_and_raises_oxygen():
    game = scenario(player(hand=["towing_a_comet"]), player(), tiles=[ocean(name) for name in OCEAN_AREAS[:9]])

    pick(game, "Play Towing a Comet")

    assert resources(game, 0)["plants"] == 2
    assert game.player_view(0)["oxygen"] == 1
    assert player_board(game, 0)["terraform_rating"] == 21
    assert game.decision["kind"] == "action"


def test_towing_a_comet_has_no_victory_points():
    game = scenario(player(played_cards=["towing_a_comet"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
