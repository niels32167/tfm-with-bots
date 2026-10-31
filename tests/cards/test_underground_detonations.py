"""#202 Underground Detonations (6 MegaCredits, building Tag): Action: spend 10 MegaCredits to
increase your heat Production 2 steps."""

from tests.helpers import final_scores, offered, pick, player, production, resources, scenario, terraformed_mars


def test_underground_detonations_has_no_requirements_and_does_nothing_when_played():
    game = scenario(player(megacredits=6, hand=["underground_detonations"]), player())

    pick(game, "Play Underground Detonations (6 MegaCredits)")

    assert resources(game, 0)["megacredits"] == 0
    assert production(game, 0)["heat"] == 0


def test_underground_detonations_action_spends_10_megacredits_to_raise_heat_production_2_steps():
    game = scenario(player(megacredits=10, played_cards=["underground_detonations"]), player())

    pick(game, "Use the action of Underground Detonations")

    assert resources(game, 0)["megacredits"] == 0
    assert production(game, 0)["heat"] == 2


def test_underground_detonations_action_needs_10_megacredits_and_steel_does_not_pay_for_it():
    game = scenario(player(megacredits=9, steel=5, played_cards=["underground_detonations"]), player())

    assert not offered(game, type="use_action")


def test_robotic_workforce_cannot_copy_underground_detonations_whose_production_box_is_its_action():
    holding = player(hand=["robotic_workforce"], played_cards=["underground_detonations"])

    assert not offered(scenario(holding, player()), "Play Robotic Workforce")


def test_underground_detonations_has_no_victory_points():
    game = scenario(player(played_cards=["underground_detonations"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
