"""The final Greenery conversion: after the final Production phase, Players may convert plants
into Greeneries, in player order from the first player, each finishing before the next."""

from tests.helpers import (
    LAND_AREAS,
    area,
    end_the_generation,
    greenery,
    labels,
    pick,
    player,
    player_board,
    resources,
    scenario,
    terraformed_mars,
)


def test_after_the_final_production_phase_the_first_player_may_convert_plants_into_a_greenery():
    game = scenario(player(plants=8), player(plants=8), first_player=1, **terraformed_mars())

    end_the_generation(game)

    assert not game.is_over
    assert game.player_view(0)["phase"] == "final_greenery"
    assert game.player_view(0)["current_player"] == 1
    assert game.decision["player"] == 1
    assert game.decision["kind"] == "final_greenery"
    assert game.decision["options"] == [
        {"index": 0, "label": "Convert 8 plants into a Greenery", "details": {"type": "convert_plants", "plants": 8}},
        {"index": 1, "label": "Done", "details": {"type": "done"}},
    ]


def test_a_final_greenery_is_placed_like_any_greenery_but_raises_neither_oxygen_nor_terraform_rating():
    game = scenario(player(plants=8, terraform_rating=40), player(), **terraformed_mars(tiles=[greenery("C3", 0)]))
    end_the_generation(game)

    pick(game, "Convert")

    assert game.decision["kind"] == "area"
    assert [option["details"]["area"] for option in game.decision["options"]] == ["B2", "B3", "C2", "C4", "D3", "D4"]
    pick(game, area="D3")  # one plant
    assert area(game, "D3")["tile"] == {"type": "greenery", "owner": 0}
    assert player_board(game, 0)["terraform_rating"] == 40
    assert resources(game, 0)["plants"] == 1


def test_a_player_keeps_converting_until_they_are_done():
    game = scenario(player(plants=17), player(plants=8), **terraformed_mars())
    end_the_generation(game)

    pick(game, "Convert")
    pick(game, area="C3")
    assert game.decision["player"] == 0
    assert labels(game) == ["Convert 8 plants into a Greenery", "Done"]

    pick(game, "Done")

    assert game.decision["player"] == 1
    assert resources(game, 0)["plants"] == 9
    assert "Player 1 is done converting plants." in game.log


def test_a_player_who_can_no_longer_convert_is_passed_over():
    game = scenario(player(plants=15), player(plants=8), **terraformed_mars())
    end_the_generation(game)

    pick(game, "Convert")
    pick(game, area="C3")

    assert game.decision["player"] == 1


def test_players_go_in_player_order_from_the_first_player_and_then_the_game_is_over():
    game = scenario(player(plants=8), player(plants=8), player(plants=8), first_player=2, **terraformed_mars())
    end_the_generation(game)
    order = []

    for _ in range(3):
        order.append(game.decision["player"])
        pick(game, "Done")

    assert order == [2, 0, 1]
    assert game.is_over
    game_over = game.log.index("The Game is over.")
    assert game.log[game_over - 1] == "Player 2 is done converting plants."


def test_players_without_8_plants_or_a_free_area_are_never_asked():
    every_free_area_taken = [greenery(name, owner=1) for name in LAND_AREAS]
    no_room = scenario(player(plants=8), player(plants=8), **terraformed_mars(tiles=every_free_area_taken))
    end_the_generation(no_room)
    assert no_room.is_over

    too_few_plants = scenario(player(plants=7), player(plants=8), **terraformed_mars())
    end_the_generation(too_few_plants)
    assert too_few_plants.decision["player"] == 1


def test_the_final_production_phase_can_provide_the_plants_to_convert():
    game = scenario(player(plants=4, production={"plants": 4}), player(), **terraformed_mars())

    end_the_generation(game)

    assert game.decision["kind"] == "final_greenery"
    assert game.decision["player"] == 0


def test_the_log_announces_the_final_greenery_conversion():
    game = scenario(player(), player(), first_player=1, **terraformed_mars())

    end_the_generation(game)

    terraformed = game.log.index("Mars is terraformed: Temperature, Oxygen and Oceans are all at their maximum.")
    assert game.log[terraformed - 1] == "Player 2 gains 20 MegaCredits (Terraform Rating 20 + MegaCredit Production 0)."
    assert game.log[terraformed + 1] == "Final Greenery conversion, in player order from Player 2."
