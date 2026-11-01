"""#009 Asteroid (14 MegaCredits, Event and space Tags): raise Temperature 1 step and gain 2
titanium. Remove up to 3 plants from any Player."""

from tests.helpers import final_scores, labels, pick, player, player_board, resources, scenario, terraformed_mars


def test_asteroid_raises_temperature_gains_2_titanium_and_removes_up_to_3_plants_from_the_player_picked():
    game = scenario(player(megacredits=14, hand=["asteroid"]), player(plants=5))

    pick(game, "Play Asteroid (14 MegaCredits)")
    assert labels(game) == ["Remove 3 plants from Player 2", "Remove nothing"]
    pick(game, "Remove 3 plants from Player 2")

    assert game.player_view(0)["temperature"] == -28
    assert player_board(game, 0)["terraform_rating"] == 21
    assert resources(game, 0)["titanium"] == 2
    assert resources(game, 1)["plants"] == 2
    assert game.decision["kind"] == "action"


def test_at_maximum_temperature_asteroid_still_gains_its_titanium_and_removes_plants():
    game = scenario(player(megacredits=14, hand=["asteroid"]), player(plants=1), temperature=8)

    pick(game, "Play Asteroid")
    pick(game, "Remove 1 plant from Player 2")

    assert player_board(game, 0)["terraform_rating"] == 20
    assert resources(game, 0)["titanium"] == 2
    assert resources(game, 1)["plants"] == 0


def test_asteroid_has_no_victory_points():
    game = scenario(player(played_cards=["asteroid"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
