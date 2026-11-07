"""#P03 Biofuels (Prelude Card, microbe Tag): increase your energy and plant Production 1 step. Gain 2 plants."""

from tests.helpers import player, player_board, production, resources, scenario


def test_biofuels_raises_energy_and_plant_production_and_gains_2_plants():
    game = scenario(player(prelude_cards=["biofuels"]), player(), prelude=True)

    assert (production(game, 0)["energy"], production(game, 0)["plants"]) == (1, 1)
    assert resources(game, 0)["plants"] == 2
    assert player_board(game, 0)["tags"]["microbe"] == 1
