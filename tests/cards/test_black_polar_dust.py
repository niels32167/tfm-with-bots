"""#022 Black Polar Dust (15 MegaCredits, no Tags): place an Ocean Tile. Decrease your
MegaCredit Production 2 steps and increase your heat Production 3 steps."""

from tests.helpers import (
    OCEAN_AREAS,
    area,
    areas_offered,
    ocean,
    offered,
    pick,
    player,
    player_board,
    production,
    scenario,
)


def test_black_polar_dust_places_an_ocean_and_trades_megacredit_production_for_heat_production():
    game = scenario(player(hand=["black_polar_dust"]), player())

    pick(game, "Play Black Polar Dust (15 MegaCredits)")
    assert production(game, 0)["megacredits"] == -2
    assert production(game, 0)["heat"] == 3
    assert game.decision["kind"] == "area"
    assert areas_offered(game) == OCEAN_AREAS

    pick(game, area="A2")

    assert area(game, "A2")["tile"] == {"type": "ocean", "owner": None}
    assert player_board(game, 0)["terraform_rating"] == 21
    assert game.decision["kind"] == "action"
    assert game.player_view(0)["actions_this_turn"] == 1


def test_black_polar_dust_cannot_take_megacredit_production_below_minus_5():
    at_minus_3 = scenario(player(hand=["black_polar_dust"], production={"megacredits": -3}), player())
    at_minus_4 = scenario(player(hand=["black_polar_dust"], production={"megacredits": -4}), player())

    assert offered(at_minus_3, "Play Black Polar Dust")
    assert not offered(at_minus_4, "Play Black Polar Dust")


def test_once_9_oceans_are_placed_black_polar_dust_only_changes_production():
    game = scenario(player(hand=["black_polar_dust"]), player(), tiles=[ocean(name) for name in OCEAN_AREAS[:9]])

    pick(game, "Play Black Polar Dust")

    assert game.decision["kind"] == "action"
    assert production(game, 0)["heat"] == 3
    assert player_board(game, 0)["terraform_rating"] == 20
    assert "All 9 Oceans are already placed, so no Ocean is placed." in game.log
