"""#080 Giant Ice Asteroid (36 MegaCredits, Event and space Tags): raise Temperature 2 steps and
place 2 Ocean Tiles. Remove up to 6 plants from any Player."""

from tests.helpers import final_scores, pick, player, player_board, resources, scenario, terraformed_mars


def test_giant_ice_asteroid_raises_temperature_2_steps_places_2_oceans_then_removes_up_to_6_plants():
    game = scenario(player(megacredits=36, hand=["giant_ice_asteroid"]), player(plants=6))

    pick(game, "Play Giant Ice Asteroid (36 MegaCredits)")
    pick(game, area="A2")
    pick(game, area="A4")
    pick(game, "Remove 6 plants from Player 2")

    assert game.player_view(0)["temperature"] == -26
    assert game.player_view(0)["oceans"] == 2
    assert player_board(game, 0)["terraform_rating"] == 24
    assert resources(game, 1)["plants"] == 0
    assert game.decision["kind"] == "action"


def test_giant_ice_asteroid_has_no_victory_points():
    game = scenario(player(played_cards=["giant_ice_asteroid"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
