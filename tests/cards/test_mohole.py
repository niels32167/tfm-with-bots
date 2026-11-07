"""#P22 Mohole (Prelude Card, building Tag): increase your heat Production 3 steps. Gain 3 heat."""

from tests.helpers import player, production, resources, scenario


def test_mohole_raises_heat_production_by_3_and_gains_3_heat():
    game = scenario(player(prelude_cards=["mohole"]), player(), prelude=True)

    assert production(game, 0)["heat"] == 3
    assert resources(game, 0)["heat"] == 3
