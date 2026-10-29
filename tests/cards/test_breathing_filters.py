"""#114 Breathing Filters (11 MegaCredits, science Tag, 2 Victory Points): requires 7 % Oxygen."""

from tests.helpers import final_scores, offered, pick, played_cards, player, resources, scenario, terraformed_mars


def test_breathing_filters_needs_7_percent_oxygen():
    assert not offered(scenario(player(hand=["breathing_filters"]), player(), oxygen=6), "Play Breathing Filters")
    assert offered(scenario(player(hand=["breathing_filters"]), player(), oxygen=7), "Play Breathing Filters")


def test_breathing_filters_does_nothing_but_score():
    game = scenario(player(megacredits=11, hand=["breathing_filters"]), player(), oxygen=7)

    pick(game, "Play Breathing Filters (11 MegaCredits)")

    assert played_cards(game, 0) == ["breathing_filters"]
    assert resources(game, 0)["megacredits"] == 0
    assert game.decision["kind"] == "action"


def test_breathing_filters_is_worth_2_victory_points():
    game = scenario(player(played_cards=["breathing_filters"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [2, 0]
