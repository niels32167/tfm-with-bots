"""#053 Lake Marineris (18 MegaCredits, no Tags, 2 Victory Points): requires 0 °C or warmer.
Place 2 Ocean Tiles."""

from tests.helpers import (
    OCEAN_AREAS,
    area,
    areas_offered,
    final_scores,
    ocean,
    offered,
    pick,
    player,
    player_board,
    resources,
    scenario,
    terraformed_mars,
)


def test_lake_marineris_needs_0_degrees_or_warmer():
    assert not offered(scenario(player(hand=["lake_marineris"]), player(), temperature=-2), "Play Lake Marineris")
    assert offered(scenario(player(hand=["lake_marineris"]), player(), temperature=0), "Play Lake Marineris")


def test_lake_marineris_places_2_oceans_one_after_the_other():
    game = scenario(player(megacredits=18, hand=["lake_marineris"]), player(), temperature=0)

    pick(game, "Play Lake Marineris")
    pick(game, area="A5")
    assert game.decision["kind"] == "area"
    assert "A5" not in areas_offered(game)
    pick(game, area="A4")  # next to the Ocean on A5

    assert area(game, "A5")["tile"]["type"] == area(game, "A4")["tile"]["type"] == "ocean"
    assert player_board(game, 0)["terraform_rating"] == 22
    assert resources(game, 0)["megacredits"] == 2
    assert game.decision["kind"] == "action"


def test_with_8_oceans_placed_lake_marineris_places_the_last_one():
    game = scenario(
        player(hand=["lake_marineris"]), player(), temperature=0, tiles=[ocean(name) for name in OCEAN_AREAS[:8]]
    )

    pick(game, "Play Lake Marineris")
    pick(game, area=OCEAN_AREAS[8])

    assert game.player_view(0)["oceans"] == 9
    assert player_board(game, 0)["terraform_rating"] == 21
    assert "All 9 Oceans are already placed, so no Ocean is placed." in game.log
    assert game.decision["kind"] == "action"


def test_lake_marineris_is_worth_2_victory_points():
    game = scenario(player(played_cards=["lake_marineris"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [2, 0]
