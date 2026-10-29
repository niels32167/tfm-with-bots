"""The fuzzer's invariants catch what they should. Each test takes a real position, breaks
one thing in its view or Decision, and checks that exactly that is reported."""

from typing import Any

import pytest
import tm_engine

from tests.fuzzing.invariants import AFTER_EVERY_DECISION, AT_THE_END_OF_THE_GAME
from tests.helpers import (
    city,
    claimed,
    end_the_action_phase,
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


def area_option(area_id: str, tile: str, on: str | None = None) -> dict[str, Any]:
    """An Option of an Area Decision; `on="ocean_areas"` for a Tile that goes on other Areas than usual."""
    details = {"type": "area", "area": area_id, "tile": tile} | ({"on": on} if on else {})
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
        ("C1", "ocean", None, "1 Ocean lies on an Area reserved for nothing, but 0 cards that put one there were played"),
        ("E3", "ocean", None, "the Ocean on E3 is not on an Area reserved for Oceans or for nothing"),
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


def test_mangroves_greenery_on_an_area_reserved_for_oceans_breaks_no_invariant():
    game = scenario(player(hand=["mangrove"]), player(), temperature=4, tiles=[city("C3", owner=0)])
    pick(game, "Play Mangrove")
    assert problems(*position(game)) == []

    pick(game, area="E4")

    assert problems(*position(game)) == []


def test_a_greenery_on_an_area_reserved_for_oceans_without_a_card_that_puts_it_there_breaks_an_invariant():
    game = scenario(player(hand=["mangrove"]), player(), temperature=4)
    pick(game, "Play Mangrove")
    pick(game, area="E4")
    view, decision = position(game)
    put(view, "A4", "greenery", 0)
    put(view, "A5", "greenery", 1)

    assert problems(view, decision) == [
        "Player 1 has 2 Greeneries on Areas reserved for Oceans, but played 1 card that put one there",
        "Player 2 has 1 Greenery on Areas reserved for Oceans, but played 0 cards that put one there",
    ]


def test_mangroves_area_decision_offering_land_breaks_an_invariant():
    game = scenario(player(hand=["mangrove"]), player(), temperature=4)
    pick(game, "Play Mangrove")
    view, decision = position(game)
    decision["options"].append(area_option("C4", "greenery", on="ocean_areas"))
    decision["options"] = [option for option in decision["options"] if option["details"]["area"] != "A4"]

    assert problems(view, decision) == [
        "the Area Decision for a Greenery on an Area reserved for Oceans offers C4, where it may not go",
        "the Area Decision for a Greenery on an Area reserved for Oceans leaves out A4, where it may go",
    ]


def test_artificial_lakes_ocean_on_land_breaks_no_invariant():
    game = scenario(player(hand=["artificial_lake"]), player(), temperature=-6)
    pick(game, "Play Artificial Lake")
    assert problems(*position(game)) == []

    pick(game, area="J1")

    assert problems(*position(game)) == []


def test_more_oceans_on_land_than_cards_that_put_one_there_break_an_invariant():
    game = scenario(player(hand=["artificial_lake"]), player(), temperature=-6)
    pick(game, "Play Artificial Lake")
    pick(game, area="J1")
    view, decision = position(game)
    put(view, "C1", "ocean")

    assert problems(view, decision) == [
        "2 Oceans lie on Areas reserved for nothing, but 1 card that puts one there was played"
    ]


def test_artificial_lakes_area_decision_offering_an_area_reserved_for_oceans_breaks_an_invariant():
    game = scenario(player(hand=["artificial_lake"]), player(), temperature=-6)
    pick(game, "Play Artificial Lake")
    view, decision = position(game)
    decision["options"].append(area_option("A2", "ocean", on="land"))
    decision["options"] = [option for option in decision["options"] if option["details"]["area"] != "J1"]

    assert problems(view, decision) == [
        "the Area Decision for an Ocean on an Area reserved for nothing offers A2, where it may not go",
        "the Area Decision for an Ocean on an Area reserved for nothing leaves out J1, where it may go",
    ]


# C4 is the one Area next to both C3 and C5.
TWO_CITIES = [city("C3", owner=1), city("C5", owner=0)]


def test_urbanized_areas_city_next_to_two_cities_breaks_no_invariant():
    holding = player(hand=["urbanized_area"], production={"energy": 1})
    game = scenario(holding, player(), tiles=TWO_CITIES)
    pick(game, "Play Urbanized Area")
    assert problems(*position(game)) == []

    pick(game, area="C4")

    assert problems(*position(game)) == []


def test_a_city_next_to_two_cities_without_urbanized_area_breaks_an_invariant():
    view, decision = position(scenario(tiles=TWO_CITIES))
    put(view, "C4", "city", 0)

    assert problems(view, decision) == [
        "the Cities on C3 and C4 are next to each other",
        "the Cities on C4 and C5 are next to each other",
    ]


def test_urbanized_area_lets_only_its_own_city_lie_next_to_other_cities():
    holding = player(hand=["urbanized_area"], production={"energy": 1})
    game = scenario(holding, player(), tiles=TWO_CITIES)
    pick(game, "Play Urbanized Area")
    pick(game, area="C4")
    view, decision = position(game)
    put(view, "D4", "city", 1)  # next to C3 and C4

    assert problems(view, decision) == ["the Cities on C3 and D4 are next to each other"]


def test_urbanized_areas_area_decision_offering_an_area_next_to_one_city_breaks_an_invariant():
    holding = player(hand=["urbanized_area"], production={"energy": 1})
    game = scenario(holding, player(), tiles=TWO_CITIES)
    pick(game, "Play Urbanized Area")
    view, decision = position(game)
    decision["options"].append(area_option("C2", "city", on="next_to_two_cities"))

    assert problems(view, decision) == [
        "the Area Decision for a City next to at least 2 Cities offers C2, where it may not go"
    ]


def test_robotic_workforce_offering_a_card_it_may_not_copy_breaks_an_invariant():
    played = ["mine", "geothermal_power"]
    game = scenario(player(hand=["robotic_workforce"], played_cards=played), player(played_cards=["power_plant"]))
    pick(game, "Play Robotic Workforce")
    view, decision = position(game)
    assert problems(view, decision) == []
    # Research has no building Tag, and the Power Plant card is the other Player's.
    copy = decision["options"][0]
    for card in ("research", "power_plant"):
        decision["options"].append({**copy, "details": {"type": "copy_production_box", "card": card}})

    assert problems(view, decision) == [
        "Robotic Workforce offers to copy the production box of Research, not a building card of Player 1's",
        "Robotic Workforce offers to copy the production box of Power Plant, not a building card of Player 1's",
    ]


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


def test_a_card_in_two_places_or_in_none_breaks_an_invariant():
    view, decision = position(scenario(player(hand=["mine"]), player(played_cards=["trees"]), deck=["grass"]))
    view["players"][1]["played_cards"].append("mine")
    view["deck"].remove("grass")
    view["deck_size"] -= 1

    assert problems(view, decision) == [
        "'mine' is in 2 places: Player 1's hand and Player 2's played cards",
        "'grass' is nowhere",
    ]


def test_the_discard_pile_and_the_cards_being_bought_from_are_places_for_cards_too():
    view, decision = position(tm_engine.Game(seed=7))  # every Player is buying from the 10 cards dealt
    assert problems(view, decision) == []
    dealt = view["players"][0]["buying"]["dealt"]
    view["discard"].append(dealt[0])
    view["discard_size"] += 1
    view["players"][1]["buying"]["bought"].append(dealt[1])

    assert problems(view, decision) == [
        f"Player 2 has bought '{dealt[1]}', which was not dealt to them",
        f"'{dealt[0]}' is in 2 places: the discard pile and Player 1's cards to buy from",
    ]


def test_buying_cards_outside_the_setup_and_research_phases_breaks_an_invariant():
    view, decision = position(scenario(player(), player(), discard=["mine"]))
    view["players"][0]["buying"] = {"dealt": [], "bought": []}
    view["discard_size"] = 2

    assert problems(view, decision) == [
        "discard_size is 2, but the discard pile holds 1 card",
        "in the action phase, Player 1 is buying cards",
    ]


def test_the_cards_being_drafted_are_places_for_cards_too():
    game = scenario(player(), player())
    end_the_action_phase(game)
    game.pick(0)  # Player 2, the first player, keeps a card
    view, decision = position(game)
    assert problems(view, decision) == []
    kept, picking_from = view["players"][1]["drafting"]["kept"], view["players"][0]["drafting"]["picking_from"]
    view["discard"].append(kept[0])
    view["discard_size"] += 1
    view["players"][1]["hand"].append(picking_from[0])
    view["players"][1]["hand_size"] += 1

    assert problems(view, decision) == [
        f"'{picking_from[0]}' is in 2 places: Player 1's cards to draft from and Player 2's hand",
        f"'{kept[0]}' is in 2 places: the discard pile and Player 2's cards kept in the Draft",
    ]


def test_drafting_cards_outside_the_draft_breaks_an_invariant():
    view, decision = position(scenario(player(), player()))
    view["players"][1]["drafting"] = {"picking_from": [], "kept": [], "passing_to": 0}

    assert problems(view, decision) == ["in the action phase, Player 2 is drafting cards"]


def test_a_corporation_or_an_unknown_card_among_the_cards_breaks_an_invariant():
    view, decision = position(scenario(player(), player()))
    view["players"][0]["played_cards"].append("credicor")
    view["players"][1]["played_cards"].append("minne")

    assert problems(view, decision) == [
        "'credicor' is not a Project Card, but is in Player 1's played cards",
        "'minne' is not a Project Card, but is in Player 2's played cards",
    ]


def test_sizes_that_disagree_with_the_cards_break_an_invariant():
    view, decision = position(scenario(player(hand=["mine"]), player()))
    view["deck_size"] += 1
    view["players"][0]["hand_size"] = 2

    assert problems(view, decision) == [
        "deck_size is 208, but the deck holds 207 cards",
        "Player 1's hand_size is 2, but their hand holds 1 card",
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
    view["scores"][0]["awards"] += 1

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


def test_a_cards_score_part_the_played_cards_do_not_give_breaks_an_invariant():
    game = scenario(
        # Io Mining Industries: 1 Victory Point per jovian Tag, and Colonizer Training Camp
        # (2 Victory Points) has one too; the Event Technology Demonstration has none.
        player(played_cards=["io_mining_industries", "colonizer_training_camp", "technology_demonstration"]),
        player(played_cards=["trees"]),
        **terraformed_mars(),
    )
    end_the_generation(game)
    view, decision = position(game)
    assert problems_at_the_end(view, decision) == []
    assert [score["cards"] for score in view["scores"]] == [4, 1]

    view["scores"][1]["cards"] = 2
    view["scores"][1]["total"] += 1

    assert problems_at_the_end(view, decision) == [
        "Player 2's score has 2 Victory Points for Cards, but the board gives 1"
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
