"""#010 Comet (21 MegaCredits, Event and space Tags): raise Temperature 1 step and place an Ocean
Tile. Remove up to 3 plants from any Player."""

from tests.helpers import (
    OCEAN_AREAS,
    final_scores,
    ocean,
    pick,
    player,
    player_board,
    resources,
    scenario,
    terraformed_mars,
)


def test_comet_raises_temperature_places_an_ocean_then_removes_up_to_3_plants():
    game = scenario(player(megacredits=21, hand=["comet"]), player(plants=4))

    pick(game, "Play Comet (21 MegaCredits)")
    assert game.decision["kind"] == "area"
    pick(game, area="A2")
    pick(game, "Remove 3 plants from Player 2")

    assert game.player_view(0)["temperature"] == -28
    assert game.player_view(0)["oceans"] == 1
    assert player_board(game, 0)["terraform_rating"] == 22
    assert resources(game, 1)["plants"] == 1
    assert game.decision["kind"] == "action"


def test_once_9_oceans_are_placed_comet_still_raises_temperature_and_removes_plants():
    game = scenario(
        player(megacredits=21, hand=["comet"]), player(plants=3), tiles=[ocean(name) for name in OCEAN_AREAS[:9]]
    )

    pick(game, "Play Comet")
    pick(game, "Remove 3 plants from Player 2")

    assert game.player_view(0)["temperature"] == -28
    assert resources(game, 1)["plants"] == 0


def test_comet_has_no_victory_points():
    game = scenario(player(played_cards=["comet"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
