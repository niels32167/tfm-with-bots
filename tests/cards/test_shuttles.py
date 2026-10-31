"""#166 Shuttles (10 MegaCredits, space Tag, 1 Victory Point): Effect: when you play a Space card,
you pay 2 MegaCredits less for it. Requires 5 % Oxygen. Decrease your energy Production 1 step and
increase your MegaCredit Production 2 steps."""

from tests.helpers import final_scores, offered, pick, player, production, resources, scenario, terraformed_mars


def test_shuttles_needs_5_percent_oxygen():
    holding = player(megacredits=10, hand=["shuttles"], production={"energy": 1})

    assert not offered(scenario(holding, player(), oxygen=4), "Play Shuttles")
    assert offered(scenario(holding, player(), oxygen=5), "Play Shuttles")


def test_shuttles_needs_1_energy_production_to_lower():
    assert not offered(scenario(player(megacredits=10, hand=["shuttles"]), player(), oxygen=5), "Play Shuttles")


def test_shuttles_trades_1_energy_production_for_2_megacredit_production():
    game = scenario(player(megacredits=10, hand=["shuttles"], production={"energy": 1}), player(), oxygen=5)

    pick(game, "Play Shuttles (10 MegaCredits)")

    assert production(game, 0)["energy"] == 0
    assert production(game, 0)["megacredits"] == 2
    assert resources(game, 0)["megacredits"] == 0


def test_with_shuttles_a_card_with_a_space_tag_costs_2_megacredits_less():
    game = scenario(player(megacredits=8, hand=["satellites", "sponsors"], played_cards=["shuttles"]), player())

    assert offered(game, "Play Satellites (8 MegaCredits)")
    assert offered(game, "Play Sponsors (6 MegaCredits)")


def test_shuttles_is_worth_1_victory_point():
    game = scenario(player(played_cards=["shuttles"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [1, 0]
