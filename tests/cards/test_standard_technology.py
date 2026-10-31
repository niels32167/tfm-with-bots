"""#156 Standard Technology (Corporate Era, 6 MegaCredits, science Tag): Effect: after you pay for a
standard project, except selling patents, you gain 3 MegaCredits."""

import pytest

from tests.helpers import final_scores, offered, pick, player, resources, scenario, terraformed_mars


def test_standard_technology_has_no_requirements_and_costs_6_megacredits():
    game = scenario(player(megacredits=6, hand=["standard_technology"]), player())

    pick(game, "Play Standard Technology (6 MegaCredits)")

    assert resources(game, 0)["megacredits"] == 0


@pytest.mark.parametrize(
    ("project", "cost"), [("power_plant", 11), ("asteroid", 14), ("aquifer", 18), ("greenery", 23), ("city", 25)]
)
def test_with_standard_technology_a_standard_project_gives_back_3_megacredits_once_paid(project, cost):
    game = scenario(player(megacredits=cost, played_cards=["standard_technology"]), player())

    pick(game, project=project)

    assert resources(game, 0)["megacredits"] == 3
    assert "Player 1's Standard Technology takes effect." in game.log
    assert "Player 1 gains 3 MegaCredits." in game.log


def test_standard_technology_does_not_help_pay_for_the_standard_project():
    game = scenario(player(megacredits=10, played_cards=["standard_technology"]), player())

    assert not offered(game, project="power_plant")


def test_standard_technology_gives_nothing_for_selling_patents():
    game = scenario(player(megacredits=0, hand=["mine"], played_cards=["standard_technology"]), player())

    pick(game, "Sell Patents")
    pick(game, "Sell Mine")

    assert resources(game, 0)["megacredits"] == 1


def test_standard_technology_gives_nothing_for_another_players_standard_project():
    game = scenario(player(), player(megacredits=11, played_cards=["standard_technology"]), first_player=0)

    pick(game, project="power_plant")

    assert resources(game, 1)["megacredits"] == 11


def test_standard_technology_is_worth_no_victory_points():
    game = scenario(player(played_cards=["standard_technology"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
