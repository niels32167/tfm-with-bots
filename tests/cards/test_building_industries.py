"""#065 Building Industries (Corporate Era, 6 MegaCredits, building Tag): decrease your energy
Production 1 step and increase your steel Production 2 steps."""

from tests.helpers import final_scores, offered, pick, player, production, scenario, terraformed_mars


def test_building_industries_needs_1_energy_production_to_lower():
    assert not offered(scenario(player(hand=["building_industries"]), player()), "Play Building Industries")
    with_energy = scenario(player(hand=["building_industries"], production={"energy": 1}), player())
    assert offered(with_energy, "Play Building Industries")


def test_building_industries_trades_1_energy_production_for_2_steel_production():
    game = scenario(player(megacredits=6, hand=["building_industries"], production={"energy": 1}), player())

    pick(game, "Play Building Industries (6 MegaCredits)")

    assert production(game, 0)["energy"] == 0
    assert production(game, 0)["steel"] == 2
    assert "Player 1 raises their steel Production by 2." in game.log


def test_building_industries_is_worth_no_victory_points():
    game = scenario(player(played_cards=["building_industries"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
