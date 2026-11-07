"""#P32 Supplier (Prelude Card, power Tag): increase your energy Production 2 steps. Gain 4 steel."""

from tests.helpers import player, production, resources, scenario


def test_supplier_raises_energy_production_by_2_and_gains_4_steel():
    game = scenario(player(prelude_cards=["supplier"]), player(), prelude=True)

    assert production(game, 0)["energy"] == 2
    assert resources(game, 0)["steel"] == 4
