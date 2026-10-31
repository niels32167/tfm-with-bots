"""Starting a Game, from settings and a seed or from a Scenario."""

import pytest
import tm_engine

from tests.helpers import (
    TAGS_THAT_COUNT,
    area,
    city,
    claimed,
    end_the_generation,
    funded,
    greenery,
    ocean,
    player,
    player_board,
    production,
    resources,
    scenario,
    skip_buying,
)


def test_a_new_game_starts_in_generation_1_with_temperature_at_minus_30():
    game = tm_engine.Game(seed=7)

    view = game.player_view(0)
    assert view["generation"] == 1
    assert view["phase"] == "setup"  # the setup buy: see tests/rules/test_buying_cards.py
    assert view["temperature"] == -30
    assert game.seed == 7
    assert not game.is_over


def test_until_corporations_exist_every_player_starts_with_42_megacredits_and_terraform_rating_20():
    game = tm_engine.Game(seed=7)

    for index in (0, 1):
        board = player_board(game, index)
        del board["hand"], board["hand_size"], board["buying"]  # the deal: see tests/rules/test_buying_cards.py
        assert board == {
            "name": f"Player {index + 1}",
            "resources": {"megacredits": 42, "steel": 0, "titanium": 0, "plants": 0, "energy": 0, "heat": 0},
            "production": {"megacredits": 0, "steel": 0, "titanium": 0, "plants": 0, "energy": 0, "heat": 0},
            "terraform_rating": 20,
            "passed": False,
            "drafting": None,
            "card_costs": {},
            "passed_in_draft": [],
            "keeping": None,
            "played_cards": [],
            "used_actions": [],
            "next_card": None,
            "tags": dict.fromkeys(TAGS_THAT_COUNT, 0),
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
    assert resources(game, 0)["megacredits"] == 30
    assert production(game, 0)["megacredits"] == 3
    assert player_board(game, 0)["terraform_rating"] == 25
    assert resources(game, 1)["megacredits"] == 0
    assert player_board(game, 1)["terraform_rating"] == 20


def test_a_scenario_places_tiles_and_sets_oxygen():
    game = scenario(player(), player(), oxygen=5, tiles=[ocean("A2"), greenery("C3", owner=0), city("C5", owner=1)])

    view = game.player_view(0)
    assert view["oxygen"] == 5
    assert view["oceans"] == 1
    assert area(game, "A2")["tile"] == {"type": "ocean", "owner": None}
    assert area(game, "C3")["tile"] == {"type": "greenery", "owner": 0}
    assert area(game, "C5")["tile"] == {"type": "city", "owner": 1}


def test_a_scenario_gives_players_any_of_the_six_resources_and_their_production():
    game = scenario(
        player(steel=3, titanium=2, plants=8, energy=4, heat=5, production={"titanium": 1, "heat": 2}),
        player(),
    )

    assert resources(game, 0) == {"megacredits": 42, "steel": 3, "titanium": 2, "plants": 8, "energy": 4, "heat": 5}
    assert production(game, 0) == {"megacredits": 0, "steel": 0, "titanium": 1, "plants": 0, "energy": 0, "heat": 2}
    assert resources(game, 1)["plants"] == 0


def test_a_scenario_terraform_rating_is_at_least_5_so_megacredits_never_go_below_zero():
    # MegaCredit Production stops at -5, so a Terraform Rating of 5 keeps every
    # Production phase's MegaCredits at 0 or more.
    game = scenario(player(megacredits=0, terraform_rating=5, production={"megacredits": -5}), player())
    end_the_generation(game)
    assert resources(game, 0)["megacredits"] == 0

    with pytest.raises(ValueError, match="Player 2's Terraform Rating must be 5 or more, not 4"):
        scenario(player(), player(terraform_rating=4))


def test_a_scenario_with_an_unknown_resource_is_rejected():
    with pytest.raises(ValueError, match="plantz"):
        scenario({"resources": {"plantz": 3}}, player())
    with pytest.raises(ValueError, match="plantz"):
        scenario(player(production={"plantz": 3}), player())


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


def test_a_scenario_claims_each_milestone_at_most_once_and_at_most_three_in_all():
    with pytest.raises(ValueError, match="Mayor Milestone can be claimed only once"):
        scenario(milestones=[claimed("mayor", by=0), claimed("mayor", by=1)])
    with pytest.raises(ValueError, match="at most 3 Milestones"):
        scenario(milestones=[claimed(name, by=0) for name in ["terraformer", "mayor", "gardener", "builder"]])
    with pytest.raises(ValueError, match="whoever claimed Mayor must be one of the Players, indexed 0 to 1"):
        scenario(milestones=[claimed("mayor", by=2)])
    with pytest.raises(ValueError, match="mayer"):
        scenario(milestones=[claimed("mayer", by=0)])


def test_a_scenario_funds_each_award_at_most_once_and_at_most_three_in_all():
    with pytest.raises(ValueError, match="Miner Award can be funded only once"):
        scenario(awards=[funded("miner", by=0), funded("miner", by=1)])
    with pytest.raises(ValueError, match="at most 3 Awards"):
        scenario(awards=[funded(name, by=0) for name in ["landlord", "banker", "scientist", "miner"]])
    with pytest.raises(ValueError, match="whoever funded Miner must be one of the Players, indexed 0 to 1"):
        scenario(awards=[funded("miner", by=2)])


def test_an_empty_scenario_is_a_new_two_player_game_with_player_1_as_first_player_and_no_cards_dealt():
    view = scenario().full_view()
    new_game = tm_engine.Game(seed=0)
    skip_buying(new_game)
    new_game = new_game.full_view()

    assert view["first_player"] == 0
    assert view["current_player"] == 0
    assert view["deck_size"] == 208
    assert all(board["hand"] == [] for board in view["players"])
    whose_turn = {"first_player": 0, "current_player": 0}
    assert {**without_cards(view), **whose_turn} == {**without_cards(new_game), **whose_turn}


def without_cards(view):
    """A view without the deck, the discard pile, the hands and the Planner Milestone's counts of
    cards in hand."""
    del view["deck"], view["deck_size"], view["discard"], view["discard_size"]
    for board in view["players"]:
        del board["hand"], board["hand_size"], board["buying"]
    for entry in view["milestones"]:
        if entry["milestone"] == "planner":
            del entry["counts"]
    return view


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
