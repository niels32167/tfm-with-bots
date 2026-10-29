"""#180 Fuel Factory (Corporate Era, 6 MegaCredits, building Tag): decrease your energy Production
1 step and increase your titanium and your MegaCredit Production 1 step each."""

from tests.helpers import final_scores, offered, pick, player, production, resources, scenario, terraformed_mars


def test_fuel_factory_needs_1_energy_production_to_lower():
    assert not offered(scenario(player(hand=["fuel_factory"]), player()), "Play Fuel Factory")


def test_fuel_factory_trades_1_energy_production_for_1_titanium_and_1_megacredit_production():
    game = scenario(player(megacredits=6, hand=["fuel_factory"], production={"energy": 1}), player())

    pick(game, "Play Fuel Factory (6 MegaCredits)")

    assert production(game, 0)["energy"] == 0
    assert production(game, 0)["titanium"] == 1
    assert production(game, 0)["megacredits"] == 1
    assert resources(game, 0)["megacredits"] == 0


def test_fuel_factory_is_worth_no_victory_points():
    game = scenario(player(played_cards=["fuel_factory"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
