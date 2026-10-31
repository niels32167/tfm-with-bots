"""#013 Space Elevator (Corporate Era, 27 MegaCredits, building and space Tags, 2 Victory Points):
Action: spend 1 steel to gain 5 MegaCredits. Increase your titanium Production 1 step."""

from tests.helpers import final_scores, offered, pick, player, production, resources, scenario, terraformed_mars


def test_space_elevator_has_no_requirements_and_raises_titanium_production_1_step():
    game = scenario(player(megacredits=27, hand=["space_elevator"]), player())

    pick(game, "Play Space Elevator (27 MegaCredits)")

    assert production(game, 0)["titanium"] == 1
    assert resources(game, 0)["megacredits"] == 0


def test_space_elevators_action_spends_1_steel_to_gain_5_megacredits():
    game = scenario(player(megacredits=1, steel=3, played_cards=["space_elevator"]), player())

    pick(game, "Use the action of Space Elevator")

    assert resources(game, 0)["steel"] == 2
    assert resources(game, 0)["megacredits"] == 6
    assert "Player 1 loses 1 steel." in game.log
    assert "Player 1 gains 5 MegaCredits." in game.log


def test_space_elevators_action_needs_1_steel():
    assert not offered(scenario(player(played_cards=["space_elevator"]), player()), type="use_action")


def test_robotic_workforce_copies_space_elevators_titanium_production_box():
    holding = player(megacredits=9, hand=["robotic_workforce"], played_cards=["space_elevator"])
    game = scenario(holding, player())

    pick(game, "Play Robotic Workforce")

    assert production(game, 0)["titanium"] == 1


def test_space_elevator_is_worth_2_victory_points():
    game = scenario(player(played_cards=["space_elevator"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [2, 0]
