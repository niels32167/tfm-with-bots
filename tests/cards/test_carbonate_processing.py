"""#043 Carbonate Processing (6 MegaCredits, building Tag): decrease your energy Production 1 step
and increase your heat Production 3 steps."""

from tests.helpers import final_scores, offered, pick, player, production, scenario, terraformed_mars


def test_carbonate_processing_needs_1_energy_production_to_lower():
    assert not offered(scenario(player(hand=["carbonate_processing"]), player()), "Play Carbonate Processing")
    with_energy = scenario(player(hand=["carbonate_processing"], production={"energy": 1}), player())
    assert offered(with_energy, "Play Carbonate Processing")


def test_carbonate_processing_trades_1_energy_production_for_3_heat_production():
    game = scenario(player(hand=["carbonate_processing"], production={"energy": 1}), player())

    pick(game, "Play Carbonate Processing (6 MegaCredits)")

    assert production(game, 0)["energy"] == 0
    assert production(game, 0)["heat"] == 3
    assert "Player 1 lowers their energy Production by 1." in game.log


def test_carbonate_processing_is_worth_no_victory_points():
    game = scenario(player(played_cards=["carbonate_processing"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
