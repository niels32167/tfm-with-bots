"""#P19 Metal-Rich Asteroid (Prelude Card): increase Temperature 1 step. Gain 4 titanium and 4 steel."""

from tests.helpers import player, player_board, resources, scenario


def test_metal_rich_asteroid_raises_temperature_and_gains_4_titanium_and_4_steel():
    game = scenario(player(prelude_cards=["metal_rich_asteroid"]), player(), prelude=True)

    assert game.full_view()["temperature"] == -28
    assert player_board(game, 0)["terraform_rating"] == 21
    assert (resources(game, 0)["titanium"], resources(game, 0)["steel"]) == (4, 4)
