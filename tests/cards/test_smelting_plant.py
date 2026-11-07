"""#P30 Smelting Plant (Prelude Card, building Tag): raise Oxygen 2 steps. Gain 5 steel."""

from tests.helpers import player, player_board, resources, scenario


def test_smelting_plant_raises_oxygen_2_steps_and_gains_5_steel():
    game = scenario(player(prelude_cards=["smelting_plant"]), player(), prelude=True)

    assert game.full_view()["oxygen"] == 2
    assert player_board(game, 0)["terraform_rating"] == 22
    assert resources(game, 0)["steel"] == 5
