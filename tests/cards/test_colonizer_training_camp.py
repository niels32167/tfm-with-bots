"""#001 Colonizer Training Camp (8 MegaCredits, building and jovian Tags, 2 Victory Points):
Oxygen must be 5 % or less. No other effect."""

from tests.helpers import final_scores, offered, pick, played_cards, player, resources, scenario, terraformed_mars


def test_colonizer_training_camp_needs_oxygen_at_5_percent_or_less():
    assert offered(scenario(player(hand=["colonizer_training_camp"]), player(), oxygen=5), "Play Colonizer")
    assert not offered(scenario(player(hand=["colonizer_training_camp"]), player(), oxygen=6), "Play Colonizer")


def test_colonizer_training_camp_does_nothing_but_cost_8_megacredits():
    game = scenario(player(megacredits=10, hand=["colonizer_training_camp"]), player())

    pick(game, "Play Colonizer Training Camp")

    assert resources(game, 0)["megacredits"] == 2
    assert played_cards(game, 0) == ["colonizer_training_camp"]


def test_colonizer_training_camp_is_worth_2_victory_points():
    game = scenario(player(played_cards=["colonizer_training_camp"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [2, 0]
