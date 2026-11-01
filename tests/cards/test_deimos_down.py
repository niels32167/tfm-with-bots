"""#039 Deimos Down (31 MegaCredits, Event and space Tags): raise Temperature 3 steps and gain 4
steel. Remove up to 8 plants from any Player."""

from tests.helpers import final_scores, labels, pick, player, player_board, resources, scenario, terraformed_mars


def test_deimos_down_raises_temperature_3_steps_gains_4_steel_and_removes_up_to_8_plants():
    game = scenario(player(megacredits=31, hand=["deimos_down"]), player(plants=10))

    pick(game, "Play Deimos Down (31 MegaCredits)")
    pick(game, "Remove 8 plants from Player 2")

    assert game.player_view(0)["temperature"] == -24
    assert player_board(game, 0)["terraform_rating"] == 23
    assert resources(game, 0)["steel"] == 4
    assert resources(game, 1)["plants"] == 2


def test_deimos_down_reaching_0_degrees_places_the_ocean_before_the_plants_are_removed():
    game = scenario(player(megacredits=31, hand=["deimos_down"]), player(plants=8), temperature=-2)

    pick(game, "Play Deimos Down")
    assert game.decision["kind"] == "area"
    pick(game, area="A2")

    assert labels(game) == ["Remove 8 plants from Player 2", "Remove nothing"]


def test_deimos_down_has_no_victory_points():
    game = scenario(player(played_cards=["deimos_down"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
