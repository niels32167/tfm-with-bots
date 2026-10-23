"""The fuzzer's invariants catch what they should. Each test takes a real position, breaks
one thing in its view or Decision, and checks that exactly that is reported."""

from typing import Any

import pytest
import tm_engine

from tests.fuzzing.invariants import AFTER_EVERY_DECISION, AT_THE_END_OF_THE_GAME
from tests.helpers import (
    city,
    claimed,
    end_the_generation,
    funded,
    greenery,
    ocean,
    pick,
    player,
    scenario,
    terraformed_mars,
)


def position(game: tm_engine.Game) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """What the fuzzer checks after a Decision: the full view and the Decision waiting next."""
    return game.full_view(), game.decision


def problems(view: dict[str, Any], decision: dict[str, Any] | None) -> list[str]:
    return [problem for check in AFTER_EVERY_DECISION for problem in check(view, decision)]


def problems_at_the_end(view: dict[str, Any], decision: dict[str, Any] | None) -> list[str]:
    return [problem for check in AT_THE_END_OF_THE_GAME for problem in check(view, decision)]


def put(view: dict[str, Any], area_id: str, tile: str, owner: int | None = None) -> None:
    """Writes a Tile onto a free Area of the view's board, whatever the rules say. An Ocean
    also counts on the Ocean track, so that only the Tile's place is wrong."""
    (entry,) = [entry for entry in view["board"] if entry["area"] == area_id]
    assert entry["tile"] is None, f"{area_id} already has a Tile"
    entry["tile"] = {"type": tile, "owner": owner}
    if tile == "ocean":
        view["oceans"] += 1


def area_option(area_id: str, tile: str) -> dict[str, Any]:
    details = {"type": "area", "area": area_id, "tile": tile}
    return {"index": 99, "label": f"Place the {tile} on {area_id}", "details": details}


def test_positions_reached_by_the_rules_break_no_invariant():
    game = scenario(
        player(plants=8),
        player(),
        tiles=[ocean("A2"), city("C3", owner=1), greenery("D4", owner=0)],
        milestones=[claimed("mayor", by=1)],
        awards=[funded("banker", by=0)],
    )
    assert problems(*position(game)) == []

    pick(game, "Convert 8 plants")

    assert position(game)[1]["kind"] == "area"
    assert problems(*position(game)) == []


def test_a_negative_resource_breaks_an_invariant():
    view, decision = position(scenario())
    view["players"][1]["resources"]["heat"] = -1
    view["players"][0]["resources"]["megacredits"] = -3

    assert problems(view, decision) == ["Player 1 has -3 MegaCredits", "Player 2 has -1 heat"]


def test_production_below_its_limit_breaks_an_invariant():
    view, decision = position(scenario())
    view["players"][0]["production"]["megacredits"] = -6
    view["players"][1]["production"]["megacredits"] = -5
    view["players"][1]["production"]["plants"] = -1

    assert problems(view, decision) == [
        "Player 1's MegaCredit Production is -6, below its limit of -5",
        "Player 2's plant Production is -1, below its limit of 0",
    ]


def test_global_parameters_off_their_tracks_break_an_invariant():
    view, decision = position(scenario(tiles=[ocean("A2")]))
    view.update(temperature=-29, oxygen=15, oceans=10)

    assert problems(view, decision) == [
        "Temperature is -29 °C, not a step on the track from -30 to 8 °C",
        "Oxygen is 15 %, not on the track from 0 to 14 %",
        "Oceans are at 10, not on the track from 0 to 9",
        "Oceans are at 10, but the board has 1 Ocean Tile",
    ]


@pytest.mark.parametrize(
    ("area_id", "tile", "owner", "problem"),
    [
        ("C1", "ocean", None, "the Ocean on C1 is not on an Area reserved for Oceans"),
        ("A4", "city", 0, "the City on A4 is not on an Area of Mars that is reserved for nothing"),
        ("E3", "greenery", 0, "the Greenery on E3 is not on an Area of Mars that is reserved for nothing"),
        (
            "phobos_space_haven",
            "city",
            1,
            "the City on phobos_space_haven is not on an Area of Mars that is reserved for nothing",
        ),
        ("C4", "city", 1, "the Cities on C3 and C4 are next to each other"),
        ("A5", "ocean", 1, "the Ocean on A5 belongs to Player 2, but Oceans belong to nobody"),
        ("H3", "city", None, "the City on H3 belongs to no Player in the Game"),
        ("H3", "greenery", 2, "the Greenery on H3 belongs to no Player in the Game"),
    ],
)
def test_a_tile_where_the_rules_never_allow_one_breaks_an_invariant(area_id, tile, owner, problem):
    view, decision = position(scenario(tiles=[ocean("A2"), city("C3", owner=0), greenery("D4", owner=1)]))
    put(view, area_id, tile, owner)

    assert problems(view, decision) == [problem]


def test_an_area_decision_that_leaves_out_a_legal_area_breaks_an_invariant():
    game = scenario(player(megacredits=30), player())
    pick(game, "City")
    view, decision = position(game)
    decision["options"] = [option for option in decision["options"] if option["details"]["area"] != "C3"]

    assert problems(view, decision) == ["the Area Decision for a City leaves out C3, where it may go"]


def test_an_area_decision_that_offers_an_illegal_area_breaks_an_invariant():
    game = scenario(player(megacredits=30), player(), tiles=[city("C3", owner=1)])
    pick(game, "City")
    view, decision = position(game)
    decision["options"].append(area_option("C4", "city"))

    assert problems(view, decision) == ["the Area Decision for a City offers C4, where it may not go"]


def test_a_greenery_offered_away_from_its_owners_tiles_when_it_could_go_next_to_them_breaks_an_invariant():
    game = scenario(player(plants=8), player(), tiles=[city("C3", owner=0)])
    pick(game, "Convert 8 plants")
    view, decision = position(game)
    decision["options"].append(area_option("H2", "greenery"))

    assert problems(view, decision) == ["the Area Decision for a Greenery offers H2, where it may not go"]


def test_more_than_three_milestones_claimed_or_awards_funded_break_an_invariant():
    game = scenario(
        milestones=[claimed(name, by=0) for name in ("terraformer", "mayor", "gardener")],
        awards=[funded(name, by=1) for name in ("landlord", "banker", "miner")],
    )
    view, decision = position(game)
    assert problems(view, decision) == []

    view["milestones"][3]["claimed_by"] = 1
    view["awards"][3]["funded_by"] = 0

    assert problems(view, decision) == [
        "4 Milestones are claimed, but at most 3 may be",
        "4 Awards are funded, but at most 3 may be",
    ]


def test_a_wrong_price_for_a_milestone_or_award_breaks_an_invariant():
    view, decision = position(scenario(awards=[funded("banker", by=0)]))
    view["milestone_cost"] = None
    view["award_cost"] = 8

    assert problems(view, decision) == [
        "with 0 Milestones claimed, milestone_cost is None, not 8",
        "with 1 Award funded, award_cost is 8, not 14",
    ]


def test_a_decision_with_no_option_breaks_an_invariant():
    view, decision = position(scenario())
    decision["options"] = []

    assert problems(view, decision) == ["Player 1's action Decision offers no Option"]


def test_a_game_that_is_not_over_must_wait_on_a_decision_and_one_that_is_over_must_not():
    view, decision = position(scenario())
    assert problems(view, None) == ["the Game is not over, but waits on no Decision"]

    view["phase"] = "over"
    assert problems(view, decision) == ["the Game is over, but still waits on a Decision"]


def finished_game() -> tm_engine.Game:
    game = scenario(
        player(terraform_rating=30, megacredits=10),
        player(terraform_rating=30, megacredits=12),
        player(),
        **terraformed_mars(tiles=[city("C3", owner=0), greenery("C4", owner=1)]),
        awards=[funded("landlord", by=0)],
    )
    end_the_generation(game)
    assert game.is_over
    return game


def test_a_finished_game_whose_score_breakdown_adds_up_breaks_no_invariant():
    assert problems_at_the_end(*position(finished_game())) == []


def test_a_score_breakdown_that_does_not_add_up_breaks_an_invariant():
    view, decision = position(finished_game())
    view["scores"][0]["cards"] += 1

    # Terraform Rating 30, 5 for sharing first place in Landlord and 1 for the City next to a Greenery.
    assert problems_at_the_end(view, decision) == ["Player 1's score adds up to 37, but its total is 36"]


def test_a_score_part_the_board_does_not_give_breaks_an_invariant():
    view, decision = position(finished_game())
    score = view["scores"][2]  # Player 3 owns no Tiles and claimed no Milestone.
    score["milestones"] += 5
    score["greeneries"] += 1
    score["cities"] += 1
    score["total"] += 7

    assert problems_at_the_end(view, decision) == [
        "Player 3's score has 5 Victory Points for Milestones, but the board gives 0",
        "Player 3's score has 1 Victory Point for Greeneries, but the board gives 0",
        "Player 3's score has 1 Victory Point for Cities, but the board gives 0",
    ]


def test_a_score_that_does_not_match_the_player_board_breaks_an_invariant():
    view, decision = position(finished_game())
    view["scores"][2]["terraform_rating"] += 1
    view["scores"][2]["total"] += 1
    view["scores"][2]["megacredits"] = 0

    assert problems_at_the_end(view, decision) == [
        "Player 3's score has Terraform Rating 21, but their board has 20",
        "Player 3's score has 0 MegaCredits, but their board has 62",
    ]


def test_a_rank_out_of_order_breaks_an_invariant():
    view, decision = position(finished_game())
    view["scores"][0]["rank"], view["scores"][1]["rank"] = view["scores"][1]["rank"], view["scores"][0]["rank"]

    assert problems_at_the_end(view, decision) == [
        "Player 1 has rank 1, but 1 Player ranks above them",
        "Player 2 has rank 2, but 0 Players rank above them",
    ]


def test_a_finished_game_without_scores_breaks_an_invariant():
    view, decision = position(finished_game())
    view["scores"] = None

    assert problems_at_the_end(view, decision) == ["the Game is over, but has no scores"]
