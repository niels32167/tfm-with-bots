"""#076 Space Mirrors (3 MegaCredits, power and space Tags): Action: spend 7 MegaCredits to increase
your energy Production 1 step."""

from tests.helpers import final_scores, offered, pick, player, production, resources, scenario, terraformed_mars


def test_space_mirrors_has_no_requirements_and_does_nothing_when_played():
    game = scenario(player(megacredits=3, hand=["space_mirrors"]), player())

    pick(game, "Play Space Mirrors (3 MegaCredits)")

    assert resources(game, 0)["megacredits"] == 0
    assert production(game, 0)["energy"] == 0


def test_space_mirrors_action_spends_7_megacredits_to_raise_energy_production_1_step():
    game = scenario(player(megacredits=8, played_cards=["space_mirrors"]), player())

    pick(game, "Use the action of Space Mirrors")

    assert resources(game, 0)["megacredits"] == 1
    assert production(game, 0)["energy"] == 1


def test_space_mirrors_action_needs_7_megacredits_and_titanium_does_not_pay_for_it():
    game = scenario(player(megacredits=6, titanium=5, played_cards=["space_mirrors"]), player())

    assert not offered(game, type="use_action")


def test_space_mirrors_has_no_victory_points():
    game = scenario(player(played_cards=["space_mirrors"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
