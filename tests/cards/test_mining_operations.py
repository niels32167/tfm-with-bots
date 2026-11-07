"""#P21 Mining Operations (Prelude Card, building Tag): increase your steel Production 2 steps. Gain 4 steel."""

from tests.helpers import player, production, resources, scenario


def test_mining_operations_raises_steel_production_by_2_and_gains_4_steel():
    game = scenario(player(prelude_cards=["mining_operations"]), player(), prelude=True)

    assert production(game, 0)["steel"] == 2
    assert resources(game, 0)["steel"] == 4
