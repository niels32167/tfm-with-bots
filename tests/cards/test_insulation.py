"""#152 Insulation (2 MegaCredits, no Tags): decrease your heat Production any number of steps and
increase your MegaCredit Production the same number of steps."""

from tests.helpers import final_scores, labels, offered, pick, player, production, resources, scenario, terraformed_mars


def test_insulation_needs_heat_production_to_lower():
    assert not offered(scenario(player(hand=["insulation"]), player()), "Play Insulation")
    assert offered(scenario(player(hand=["insulation"], production={"heat": 1}), player()), "Play Insulation")


def test_insulation_asks_how_many_steps_of_heat_production_to_trade_from_1_up_to_all_of_it():
    game = scenario(player(megacredits=2, hand=["insulation"], production={"heat": 3}), player())

    pick(game, "Play Insulation (2 MegaCredits)")

    assert resources(game, 0)["megacredits"] == 0
    assert game.decision["kind"] == "production"
    assert labels(game) == [
        "Raise MegaCredit Production by 1 and lower heat Production by 1",
        "Raise MegaCredit Production by 2 and lower heat Production by 2",
        "Raise MegaCredit Production by 3 and lower heat Production by 3",
    ]
    assert offered(game, type="choose_production", card="insulation")


def test_insulation_trades_the_chosen_steps_of_heat_production_for_megacredit_production():
    game = scenario(player(hand=["insulation"], production={"heat": 3, "megacredits": -2}), player())

    pick(game, "Play Insulation")
    pick(game, "Raise MegaCredit Production by 2 and lower heat Production by 2")

    assert production(game, 0)["heat"] == 1
    assert production(game, 0)["megacredits"] == 0
    assert "Player 1 lowers their heat Production by 2." in game.log
    assert "Player 1 raises their MegaCredit Production by 2." in game.log
    assert game.decision["kind"] == "action"


def test_with_1_heat_production_insulation_trades_it_without_a_decision():
    game = scenario(player(hand=["insulation"], production={"heat": 1}), player())

    pick(game, "Play Insulation")

    assert production(game, 0)["heat"] == 0
    assert production(game, 0)["megacredits"] == 1
    assert game.decision["kind"] == "action"


def test_insulation_is_worth_no_victory_points():
    game = scenario(player(played_cards=["insulation"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
