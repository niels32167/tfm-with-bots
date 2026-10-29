"""#098 Tropical Resort (Corporate Era, 13 MegaCredits, building Tag, 2 Victory Points): reduce your
heat Production 2 steps and increase your MegaCredit Production 3 steps."""

from tests.helpers import final_scores, offered, pick, player, production, scenario, terraformed_mars


def test_tropical_resort_needs_2_heat_production_to_lower():
    one = scenario(player(hand=["tropical_resort"], production={"heat": 1}), player())
    two = scenario(player(hand=["tropical_resort"], production={"heat": 2}), player())

    assert not offered(one, "Play Tropical Resort")
    assert offered(two, "Play Tropical Resort")


def test_tropical_resort_trades_2_heat_production_for_3_megacredit_production():
    game = scenario(player(megacredits=13, hand=["tropical_resort"], production={"heat": 2}), player())

    pick(game, "Play Tropical Resort (13 MegaCredits)")

    assert production(game, 0)["heat"] == 0
    assert production(game, 0)["megacredits"] == 3
    assert "Player 1 lowers their heat Production by 2." in game.log


def test_tropical_resort_is_worth_2_victory_points():
    game = scenario(player(played_cards=["tropical_resort"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [2, 0]
