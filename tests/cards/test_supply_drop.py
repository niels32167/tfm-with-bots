"""#P33 Supply Drop (Prelude Card): gain 3 titanium, 8 steel and 3 plants."""

from tests.helpers import player, resources, scenario


def test_supply_drop_gains_3_titanium_8_steel_and_3_plants():
    game = scenario(player(prelude_cards=["supply_drop"]), player(), prelude=True)

    gained = resources(game, 0)
    assert (gained["titanium"], gained["steel"], gained["plants"]) == (3, 8, 3)
