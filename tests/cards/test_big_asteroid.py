"""#011 Big Asteroid (27 MegaCredits, Event and space Tags): raise Temperature 2 steps and gain 4
titanium. Remove up to 4 plants from any Player."""

from tests.helpers import final_scores, pick, player, player_board, resources, scenario, terraformed_mars


def test_big_asteroid_raises_temperature_2_steps_gains_4_titanium_and_removes_up_to_4_plants():
    game = scenario(player(megacredits=27, hand=["big_asteroid"]), player(plants=6))

    pick(game, "Play Big Asteroid (27 MegaCredits)")
    pick(game, "Remove 4 plants from Player 2")

    assert game.player_view(0)["temperature"] == -26
    assert player_board(game, 0)["terraform_rating"] == 22
    assert resources(game, 0)["titanium"] == 4
    assert resources(game, 1)["plants"] == 2


def test_big_asteroid_has_no_victory_points():
    game = scenario(player(played_cards=["big_asteroid"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
