"""#041 Food Factory (12 MegaCredits, building Tag, 1 Victory Point): decrease your plant Production
1 step and increase your MegaCredit Production 4 steps."""

from tests.helpers import final_scores, offered, pick, player, production, scenario, terraformed_mars


def test_food_factory_needs_1_plant_production_to_lower():
    assert not offered(scenario(player(hand=["food_factory"]), player()), "Play Food Factory")
    assert offered(scenario(player(hand=["food_factory"], production={"plants": 1}), player()), "Play Food Factory")


def test_food_factory_trades_1_plant_production_for_4_megacredit_production():
    game = scenario(player(hand=["food_factory"], production={"plants": 1}), player())

    pick(game, "Play Food Factory (12 MegaCredits)")

    assert production(game, 0)["plants"] == 0
    assert production(game, 0)["megacredits"] == 4


def test_food_factory_is_worth_1_victory_point():
    game = scenario(player(played_cards=["food_factory"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [1, 0]
