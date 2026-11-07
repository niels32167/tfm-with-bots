"""#P07 Dome Farming (Prelude Card, building and plant Tags): increase your MegaCredit Production 2
steps and plant Production 1 step."""

from tests.helpers import player, player_board, production, scenario


def test_dome_farming_raises_megacredit_production_by_2_and_plant_production_by_1():
    game = scenario(player(prelude_cards=["dome_farming"]), player(), prelude=True)

    assert (production(game, 0)["megacredits"], production(game, 0)["plants"]) == (2, 1)
    tags = player_board(game, 0)["tags"]
    assert (tags["building"], tags["plant"]) == (1, 1)
