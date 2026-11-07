"""#P36 House Printing (Prelude's Project Card, 10 MegaCredits, building Tag, 1 Victory Point): increase your steel
Production 1 step."""

from tests.helpers import final_scores, pick, played_cards, player, production, resources, scenario, terraformed_mars


def test_house_printing_raises_steel_production_1_step_and_steel_may_pay_for_it():
    game = scenario(player(megacredits=6, steel=2, hand=["house_printing"]), player(), prelude=True)

    pick(game, "Play House Printing")  # 6 MegaCredits and 2 steel, the only way to pay

    assert production(game, 0)["steel"] == 1
    assert resources(game, 0)["megacredits"] == 0
    assert played_cards(game, 0) == ["house_printing"]


def test_house_printing_is_worth_1_victory_point():
    game = scenario(player(played_cards=["house_printing"]), player(), prelude=True, **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [1, 0]
