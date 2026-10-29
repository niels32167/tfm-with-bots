"""#126 GHG Factories (11 MegaCredits, building Tag): decrease your energy Production 1 step and
increase your heat Production 4 steps."""

from tests.helpers import final_scores, offered, pick, player, production, scenario, terraformed_mars


def test_ghg_factories_needs_1_energy_production_to_lower():
    assert not offered(scenario(player(hand=["ghg_factories"]), player()), "Play GHG Factories")
    assert offered(scenario(player(hand=["ghg_factories"], production={"energy": 1}), player()), "Play GHG Factories")


def test_ghg_factories_trades_1_energy_production_for_4_heat_production():
    game = scenario(player(megacredits=11, hand=["ghg_factories"], production={"energy": 1}), player())

    pick(game, "Play GHG Factories (11 MegaCredits)")

    assert production(game, 0)["energy"] == 0
    assert production(game, 0)["heat"] == 4
    assert "Player 1 raises their heat Production by 4." in game.log


def test_ghg_factories_is_worth_no_victory_points():
    game = scenario(player(played_cards=["ghg_factories"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
