"""#P23 Mohole Excavation (Prelude Card, building Tag): increase your steel Production 1 step and heat
Production 2 steps. Gain 2 heat."""

from tests.helpers import player, production, resources, scenario


def test_mohole_excavation_raises_steel_and_heat_production_and_gains_2_heat():
    game = scenario(player(prelude_cards=["mohole_excavation"]), player(), prelude=True)

    assert (production(game, 0)["steel"], production(game, 0)["heat"]) == (1, 2)
    assert resources(game, 0)["heat"] == 2
