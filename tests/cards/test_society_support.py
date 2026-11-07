"""#P31 Society Support (Prelude Card): increase your plant, energy and heat Production 1 step.
Decrease your MegaCredit Production 1 step."""

from tests.helpers import player, player_board, production, resources, scenario


def test_society_support_raises_plant_energy_and_heat_production_and_lowers_megacredit_production():
    game = scenario(player(prelude_cards=["society_support"]), player(), prelude=True)

    changed = production(game, 0)
    assert (changed["plants"], changed["energy"], changed["heat"], changed["megacredits"]) == (1, 1, 1, -1)


def test_with_megacredit_production_at_minus_5_it_cant_be_played_and_is_discarded_for_15_megacredits():
    game = scenario(player(prelude_cards=["society_support"], production={"megacredits": -5}), player(), prelude=True)

    assert resources(game, 0)["megacredits"] == 57
    assert production(game, 0)["plants"] == 0
    assert player_board(game, 0)["played_prelude_cards"] == []
