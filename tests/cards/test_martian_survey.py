"""#P38 Martian Survey (Prelude's Event, 9 MegaCredits, science and Event Tags, 1 Victory Point): Oxygen must be 4 %
or lower. Draw two cards."""

from tests.helpers import final_scores, hand, offered, pick, player, scenario, terraformed_mars


def test_martian_survey_needs_oxygen_at_4_percent_or_lower():
    at_4 = scenario(player(megacredits=9, hand=["martian_survey"]), player(), prelude=True, oxygen=4)
    at_5 = scenario(player(megacredits=9, hand=["martian_survey"]), player(), prelude=True, oxygen=5)

    assert offered(at_4, "Play Martian Survey (9 MegaCredits)")
    assert not offered(at_5, "Play Martian Survey")


def test_martian_survey_draws_2_cards():
    game = scenario(player(megacredits=9, hand=["martian_survey"]), player(), prelude=True,
                    deck=["mine", "trees", "birds"])

    pick(game, "Play Martian Survey")

    assert hand(game, 0) == ["mine", "trees"]


def test_martian_survey_is_worth_1_victory_point_though_an_event():
    game = scenario(player(played_cards=["martian_survey"]), player(), prelude=True, **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [1, 0]
