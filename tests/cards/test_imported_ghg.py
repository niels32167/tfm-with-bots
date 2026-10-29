"""#162 Imported GHG (7 MegaCredits, Event, space and Earth Tags): increase your heat Production
1 step and gain 3 heat."""

from tests.helpers import final_scores, pick, player, production, resources, scenario, terraformed_mars


def test_imported_ghg_raises_heat_production_by_1_and_gains_3_heat():
    game = scenario(player(megacredits=7, hand=["imported_ghg"]), player())

    pick(game, "Play Imported GHG (7 MegaCredits)")

    assert production(game, 0)["heat"] == 1
    assert resources(game, 0)["heat"] == 3
    assert resources(game, 0)["megacredits"] == 0


def test_imported_ghg_may_be_paid_with_titanium_for_its_space_tag():
    # An Event's Tags count while it is being played, so its space Tag lets titanium pay.
    game = scenario(player(megacredits=1, titanium=2, hand=["imported_ghg"]), player())

    pick(game, "Play Imported GHG")

    assert resources(game, 0)["titanium"] == 0
    assert resources(game, 0)["megacredits"] == 0


def test_imported_ghg_has_no_victory_points():
    game = scenario(player(played_cards=["imported_ghg"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
