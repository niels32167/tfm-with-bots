"""#014 Development Center (Corporate Era, 11 MegaCredits, building and science Tags): Action:
spend 1 energy to draw a card."""

from tests.helpers import final_scores, hand, offered, pick, player, resources, scenario, terraformed_mars


def test_development_center_has_no_requirements_and_does_nothing_when_played():
    game = scenario(player(megacredits=11, hand=["development_center"]), player())

    pick(game, "Play Development Center (11 MegaCredits)")

    assert resources(game, 0)["megacredits"] == 0
    assert hand(game, 0) == []


def test_development_centers_action_spends_1_energy_to_draw_a_card():
    game = scenario(player(energy=2, played_cards=["development_center"]), player(), deck=["mine", "trees"])

    pick(game, "Use the action of Development Center")

    assert resources(game, 0)["energy"] == 1
    assert hand(game, 0) == ["mine"]
    assert "Player 1 draws 1 card." in game.log


def test_development_centers_action_needs_1_energy():
    assert not offered(scenario(player(played_cards=["development_center"]), player()), type="use_action")


def test_development_center_has_no_victory_points():
    game = scenario(player(played_cards=["development_center"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
