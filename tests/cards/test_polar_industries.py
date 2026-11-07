"""#P26 Polar Industries (Prelude Card, building Tag): increase your heat Production 2 steps. Place an Ocean Tile."""

from tests.helpers import area, pick, player, player_board, production, scenario


def test_polar_industries_raises_heat_production_by_2_and_places_an_ocean():
    game = scenario(player(prelude_cards=["polar_industries"]), player(), prelude=True)

    pick(game, area="A2")

    assert production(game, 0)["heat"] == 2
    assert area(game, "A2")["tile"]["type"] == "ocean"
    assert player_board(game, 0)["terraform_rating"] == 21
