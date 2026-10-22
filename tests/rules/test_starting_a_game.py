"""Starting a Game, from settings and a seed or from a Scenario."""

import pytest
import tm_engine

from tests.helpers import area, city, greenery, ocean, player, player_board, scenario


def test_a_new_game_starts_in_generation_1_with_temperature_at_minus_30():
    game = tm_engine.Game(seed=7)

    view = game.player_view(0)
    assert view["generation"] == 1
    assert view["phase"] == "action"
    assert view["temperature"] == -30
    assert game.seed == 7
    assert not game.is_over


def test_until_corporations_exist_every_player_starts_with_42_megacredits_and_terraform_rating_20():
    game = tm_engine.Game(seed=7)

    for index in (0, 1):
        assert player_board(game, index) == {
            "name": f"Player {index + 1}",
            "megacredits": 42,
            "steel": 0,
            "titanium": 0,
            "plants": 0,
            "production": {"megacredits": 0},
            "terraform_rating": 20,
            "passed": False,
        }


def test_a_game_has_two_to_five_players():
    for count in (2, 3, 4, 5):
        game = tm_engine.Game(seed=7, players=count)
        assert game.players == count
        assert len(game.player_view(0)["players"]) == count

    with pytest.raises(ValueError, match="2 to 5 Players"):
        tm_engine.Game(seed=7, players=1)
    with pytest.raises(ValueError, match="2 to 5 Players"):
        tm_engine.Game(seed=7, players=6)


def test_a_scenario_sets_the_generation_temperature_and_each_players_board():
    game = scenario(
        player(megacredits=30, production={"megacredits": 3}, terraform_rating=25),
        player(megacredits=0),
        generation=4,
        temperature=-10,
        seed=99,
    )

    view = game.player_view(0)
    assert view["generation"] == 4
    assert view["temperature"] == -10
    assert game.seed == 99
    assert player_board(game, 0)["megacredits"] == 30
    assert player_board(game, 0)["production"] == {"megacredits": 3}
    assert player_board(game, 0)["terraform_rating"] == 25
    assert player_board(game, 1)["megacredits"] == 0
    assert player_board(game, 1)["terraform_rating"] == 20


def test_a_scenario_places_tiles_and_sets_oxygen():
    game = scenario(player(), player(), oxygen=5, tiles=[ocean("A2"), greenery("C3", owner=0), city("C5", owner=1)])

    view = game.player_view(0)
    assert view["oxygen"] == 5
    assert view["oceans"] == 1
    assert area(game, "A2")["tile"] == {"type": "ocean", "owner": None}
    assert area(game, "C3")["tile"] == {"type": "greenery", "owner": 0}
    assert area(game, "C5")["tile"] == {"type": "city", "owner": 1}


def test_a_scenario_gives_players_steel_titanium_and_plants():
    game = scenario(player(steel=3, titanium=2, plants=8), player())

    board = player_board(game, 0)
    assert (board["steel"], board["titanium"], board["plants"]) == (3, 2, 8)
    assert player_board(game, 1)["plants"] == 0


def test_a_scenario_oxygen_must_be_on_the_track_from_0_to_14_percent():
    assert scenario(oxygen=14).player_view(0)["oxygen"] == 14
    with pytest.raises(ValueError, match="Oxygen"):
        scenario(oxygen=15)
    with pytest.raises(ValueError, match="Oxygen"):
        scenario(oxygen=-1)


def test_a_scenario_cannot_put_a_tile_where_the_rules_never_allow_one():
    def rejected(tile: dict, reason: str) -> None:
        with pytest.raises(ValueError, match=reason):
            scenario(player(), player(), tiles=[tile])

    rejected(ocean("C3"), "Ocean on C3, which is not reserved for Oceans")
    rejected(city("A2", owner=0), "City on A2, which is reserved for Oceans")
    rejected(greenery("E3", owner=0), "Greenery on E3, which is reserved for the Noctis City card")
    rejected(city("phobos_space_haven", owner=0), "City on phobos_space_haven, which is reserved for the Phobos")
    rejected(ocean("Z9"), "no Area 'Z9'")
    rejected({"area": "A2", "tile": "ocean", "owner": 0}, "Oceans belong to nobody")
    rejected({"area": "C3", "tile": "city"}, "a City needs an owner")
    rejected(city("C3", owner=2), "owner must be one of the Players, indexed 0 to 1")


def test_a_scenario_has_at_most_one_tile_per_area_and_at_most_9_oceans():
    with pytest.raises(ValueError, match="two Tiles on C3"):
        scenario(tiles=[city("C3", owner=0), greenery("C3", owner=1)])
    with pytest.raises(ValueError, match="at most 9 Oceans"):
        scenario(tiles=[ocean(name) for name in ["A2", "A4", "A5", "B6", "D8", "E4", "E5", "E6", "F6", "F7"]])


def test_an_empty_scenario_is_a_new_two_player_game_with_player_1_as_first_player():
    view = scenario().player_view(0)
    new_game = tm_engine.Game(seed=0).player_view(0)

    assert view["first_player"] == 0
    assert view["current_player"] == 0
    whose_turn = {"first_player": 0, "current_player": 0}
    assert {**view, **whose_turn} == {**new_game, **whose_turn}


def test_a_scenario_with_an_unknown_field_is_rejected():
    with pytest.raises(ValueError, match="megacredit"):
        scenario(player(megacredit=30), player())


def test_a_scenario_temperature_must_be_a_step_on_the_track():
    with pytest.raises(ValueError, match="Temperature"):
        scenario(temperature=-29)
    with pytest.raises(ValueError, match="Temperature"):
        scenario(temperature=10)


def test_there_is_no_player_view_for_a_player_not_in_the_game():
    game = tm_engine.Game(seed=7)

    with pytest.raises(ValueError, match="no Player with index 2"):
        game.player_view(2)


def test_a_seed_is_a_whole_number_that_every_json_reader_keeps_exactly():
    # JSON readers such as the browser's hold numbers as doubles, exact only up to 2**53 - 1.
    assert tm_engine.MAX_SEED == 2**53 - 1
    assert tm_engine.Game(seed=tm_engine.MAX_SEED).seed == tm_engine.MAX_SEED

    with pytest.raises(ValueError, match="seed"):
        tm_engine.Game(seed=tm_engine.MAX_SEED + 1)
    with pytest.raises(ValueError, match="seed"):
        scenario(seed=tm_engine.MAX_SEED + 1)
