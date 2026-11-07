"""#P41 SF Memorial (Prelude's Project Card, 7 MegaCredits, building Tag, 1 Victory Point): draw 1 card."""

from tests.helpers import final_scores, hand, pick, player, resources, scenario, terraformed_mars


def test_sf_memorial_draws_1_card():
    game = scenario(player(megacredits=7, hand=["sf_memorial"]), player(), prelude=True, deck=["mine", "trees"])

    pick(game, "Play SF Memorial (7 MegaCredits)")

    assert hand(game, 0) == ["mine"]
    assert resources(game, 0)["megacredits"] == 0


def test_sf_memorial_is_worth_1_victory_point():
    game = scenario(player(played_cards=["sf_memorial"]), player(), prelude=True, **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [1, 0]
