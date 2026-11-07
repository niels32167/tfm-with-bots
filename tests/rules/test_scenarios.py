"""What a Scenario can describe: the positions real play reaches, as the dev panel's state editor
needs them, and Game.to_scenario, which describes a Game's position as one."""

import pytest
import tm_engine

from tests.helpers import (
    MAX_PICKS,
    area,
    greenery,
    ocean,
    offered,
    pick,
    play_randomly,
    player,
    player_board,
    scenario,
)


@pytest.mark.parametrize("card", ["mangrove", "protected_valley"])
def test_a_greenery_goes_on_an_area_reserved_for_oceans_with_a_card_played_that_puts_one_there(
    card,
):
    game = scenario(
        player(played_cards=[card]), player(), tiles=[greenery("A2", owner=0)]
    )

    assert area(game, "A2")["tile"] == {"type": "greenery", "owner": 0}


def test_each_card_played_allows_one_greenery_on_an_area_reserved_for_oceans():
    game = scenario(
        player(played_cards=["mangrove", "protected_valley"]),
        player(),
        tiles=[greenery("A2", owner=0), greenery("A4", owner=0)],
    )
    assert area(game, "A4")["tile"] == {"type": "greenery", "owner": 0}

    with pytest.raises(
        ValueError, match="Greenery on A4, which is reserved for Oceans"
    ):
        scenario(
            player(played_cards=["mangrove"]),
            player(),
            tiles=[greenery("A2", owner=0), greenery("A4", owner=0)],
        )


def test_another_players_card_allows_no_greenery_on_an_area_reserved_for_oceans():
    with pytest.raises(
        ValueError, match="Greenery on A2, which is reserved for Oceans"
    ):
        scenario(
            player(), player(played_cards=["mangrove"]), tiles=[greenery("A2", owner=0)]
        )


def test_an_ocean_goes_on_land_with_artificial_lake_played_by_anyone():
    game = scenario(
        player(), player(played_cards=["artificial_lake"]), tiles=[ocean("C3")]
    )

    assert area(game, "C3")["tile"] == {"type": "ocean", "owner": None}
    assert game.full_view()["oceans"] == 1


def test_artificial_lake_allows_one_ocean_on_land():
    with pytest.raises(
        ValueError, match="Ocean on C4, which is not reserved for Oceans"
    ):
        scenario(
            player(played_cards=["artificial_lake"]),
            player(),
            tiles=[ocean("C3"), ocean("C4")],
        )


def test_artificial_lake_allows_no_ocean_on_an_area_reserved_for_a_cards_city():
    with pytest.raises(
        ValueError, match="Ocean on E3, which is not reserved for Oceans"
    ):
        scenario(
            player(played_cards=["artificial_lake"]), player(), tiles=[ocean("E3")]
        )


def test_a_scenario_says_a_players_terraform_rating_was_raised_this_generation():
    raised = scenario(
        player(
            corporation="united_nations_mars_initiative", terraform_rating_raised=True
        ),
        player(),
    )
    not_raised = scenario(
        player(corporation="united_nations_mars_initiative"), player()
    )

    assert player_board(raised, 0)["terraform_rating_raised"]
    assert offered(raised, type="use_action", card="united_nations_mars_initiative")
    assert not offered(
        not_raised, type="use_action", card="united_nations_mars_initiative"
    )


def test_a_scenario_says_which_actions_were_used_this_generation():
    used = scenario(
        player(played_cards=["restricted_area"], used_actions=["restricted_area"]),
        player(),
    )
    unused = scenario(player(played_cards=["restricted_area"]), player())

    assert player_board(used, 0)["used_actions"] == ["restricted_area"]
    assert not offered(used, type="use_action", card="restricted_area")
    assert offered(unused, type="use_action", card="restricted_area")


def test_a_scenario_says_a_corporations_action_was_used():
    game = scenario(
        player(
            corporation="united_nations_mars_initiative",
            terraform_rating_raised=True,
            used_actions=["united_nations_mars_initiative"],
        ),
        player(),
    )

    assert not offered(game, type="use_action", card="united_nations_mars_initiative")


@pytest.mark.parametrize(
    ("given", "problem"),
    [
        (
            player(used_actions=["restricted_area"]),
            "'restricted_area', which they have not played",
        ),
        (player(played_cards=["mine"], used_actions=["mine"]), "'mine' has no action"),
        (player(used_actions=["no_such_card"]), "there is no card 'no_such_card'"),
    ],
)
def test_a_scenario_refuses_an_action_used_that_could_not_have_been(given, problem):
    with pytest.raises(ValueError, match=problem):
        scenario(given, player())


def test_a_scenario_says_who_has_passed_and_they_take_no_turns():
    game = scenario(player(passed=True), player(), first_player=1)

    assert player_board(game, 0)["passed"]
    assert game.decision["player"] == 1
    pick(game, "Pass")
    assert game.full_view()["generation"] == 2


def test_a_scenario_says_whose_turn_it_is_and_how_far_into_it():
    game = scenario(player(), player(), current_player=1, actions_this_turn=1)

    view = game.full_view()
    assert view["first_player"] == 0
    assert view["current_player"] == 1
    assert view["actions_this_turn"] == 1
    assert game.decision["player"] == 1
    assert offered(game, "End Turn")


@pytest.mark.parametrize(
    ("fields", "problem"),
    [
        ({"current_player": 2}, "whose Turn it is must be one of the Players"),
        ({"actions_this_turn": 2}, "at most 1 Action"),
        ({"first_player": 0}, "Player 1 has passed, so it cannot be their Turn"),
    ],
)
def test_a_scenario_refuses_a_turn_that_could_not_be(fields, problem):
    with pytest.raises(ValueError, match=problem):
        scenario(player(passed=True), player(), **fields)


def test_a_scenario_says_an_event_waits_on_the_next_card_played():
    game = scenario(
        player(
            played_cards=["indentured_workers"],
            next_card="indentured_workers",
            hand=["mine"],
        ),
        player(),
    )

    board = player_board(game, 0)
    assert board["next_card"] == "indentured_workers"
    assert board["card_costs"]["mine"] == 0


@pytest.mark.parametrize(
    ("given", "problem"),
    [
        (
            player(next_card="indentured_workers"),
            "'indentured_workers', which they have not played",
        ),
        (
            player(played_cards=["mine"], next_card="mine"),
            "'mine' does nothing to the next card",
        ),
    ],
)
def test_a_scenario_refuses_an_effect_on_the_next_card_that_could_not_be_waiting(
    given, problem
):
    with pytest.raises(ValueError, match=problem):
        scenario(given, player())


def test_a_replay_saved_before_a_scenario_could_say_these_starts_the_turn_as_it_did():
    saved = {
        "start": {"scenario": {"players": [{}, {}], "first_player": 1, "draft": True}},
        "picks": [],
    }

    view = tm_engine.Game.from_replay(saved).full_view()

    assert view["current_player"] == 1
    assert view["actions_this_turn"] == 0
    assert not any(
        board["passed"] or board["used_actions"] or board["next_card"]
        for board in view["players"]
    )


def view_without_what_a_scenario_forgets(game: tm_engine.Game) -> dict:
    """The full view, but for the cards passed in the Draft, which change nothing in the rules."""
    view = game.full_view()
    for board in view["players"]:
        del board["passed_in_draft"]
    return view


@pytest.mark.parametrize(("players", "prelude"), [(2, False), (3, False), (5, False), (2, True), (4, True)])
def test_every_action_of_a_random_game_is_the_same_position_described_as_a_scenario(
    players, prelude
):
    game = tm_engine.Game(seed=100 + players, players=players, prelude=prelude)
    actions = 0
    for _ in range(MAX_PICKS):
        if game.is_over:
            break
        if game.decision["kind"] == "action" and game.full_view()["phase"] == "action":
            actions += 1
            described = tm_engine.Game.from_scenario(game.to_scenario())
            assert view_without_what_a_scenario_forgets(
                described
            ) == view_without_what_a_scenario_forgets(game)
            assert described.decision["options"] == game.decision["options"]
        play_randomly(game, seed=actions, picks=1)
    assert game.is_over
    assert actions > 50


@pytest.mark.parametrize("prelude", [False, True])
def test_every_position_of_a_random_game_can_be_described_as_a_scenario(prelude):
    game = tm_engine.Game(seed=9, players=4, prelude=prelude)
    for _ in range(MAX_PICKS):
        tm_engine.Game.from_scenario(game.to_scenario())
        if game.is_over:
            return
        play_randomly(game, seed=1, picks=1)
    raise AssertionError(f"the Game was not over after {MAX_PICKS} picks")


def test_a_position_described_as_a_scenario_keeps_its_cards_and_tiles_and_who_holds_what():
    game = scenario(
        player(
            megacredits=11,
            plants=3,
            production={"heat": 2},
            terraform_rating=23,
            hand=["mine"],
            played_cards=["tardigrades", "land_claim"],
            card_resources={"tardigrades": 3},
            corporation="helion",
        ),
        player(corporation="inventrix", first_action_due=True),
        generation=4,
        first_player=1,
        temperature=-10,
        oxygen=5,
        tiles=[
            ocean("A2"),
            greenery("C3", owner=0),
            {"area": "C5", "tile": "special", "card": "nuclear_zone", "owner": 0},
        ],
        land_claim={"area": "G1", "player": 0},
        milestones=[{"milestone": "mayor", "claimed_by": 1}],
        awards=[{"award": "banker", "funded_by": 0}],
        deck=["trees", "asteroid"],
        discard=["sponsors"],
        draft=False,
    )

    described = game.to_scenario()

    assert described["seed"] == game.seed
    assert described["generation"] == 4
    assert described["first_player"] == 1
    assert described["temperature"] == -10
    assert described["oxygen"] == 5
    assert described["tiles"] == [
        {"area": "A2", "tile": "ocean", "owner": None},
        {"area": "C3", "tile": "greenery", "owner": 0},
        {"area": "C5", "tile": "special", "owner": 0, "card": "nuclear_zone"},
    ]
    assert described["land_claim"] == {"area": "G1", "player": 0}
    assert described["milestones"] == [{"milestone": "mayor", "claimed_by": 1}]
    assert described["awards"] == [{"award": "banker", "funded_by": 0}]
    assert described["deck"][:2] == ["trees", "asteroid"]
    assert described["discard"] == ["sponsors"]
    assert described["draft"] is False
    first = described["players"][0]
    assert first["resources"] == {
        "megacredits": 11,
        "steel": 0,
        "titanium": 0,
        "plants": 3,
        "energy": 0,
        "heat": 0,
    }
    assert first["production"]["heat"] == 2
    assert first["terraform_rating"] == 23
    assert first["hand"] == ["mine"]
    assert sorted(first["played_cards"]) == ["land_claim", "tardigrades"]
    assert first["card_resources"] == {"tardigrades": 3}
    assert first["corporation"] == "helion"
    assert described["players"][1]["first_action_due"] is True


def test_a_position_outside_the_action_phase_is_described_at_the_start_of_a_turn():
    game = tm_engine.Game(seed=3, players=2)
    assert game.full_view()["phase"] == "setup"

    described = tm_engine.Game.from_scenario(game.to_scenario()).full_view()

    assert described["phase"] == "action"
    assert described["current_player"] == game.full_view()["first_player"]
    assert all(not board["passed"] for board in described["players"])
