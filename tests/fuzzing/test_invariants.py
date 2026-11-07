"""The fuzzer's invariants catch what they should. Each test takes a real position, breaks
one thing in its view or Decision, and checks that exactly that is reported."""

from typing import Any

import pytest
import tm_engine

from tests.fuzzing.invariants import AFTER_EVERY_DECISION, AT_THE_END_OF_THE_GAME
from tests.helpers import (
    CORPORATIONS,
    PRELUDE_CARDS,
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
    special,
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


def test_cards_looked_at_with_business_contacts_break_no_invariant():
    game = scenario(player(hand=["business_contacts"]), player(), deck=["mine", "trees", "birds", "fish"])

    pick(game, "Play Business Contacts")
    pick(game, type="keep_card", card="trees")

    assert position(game)[1]["kind"] == "keep_cards"
    assert problems(*position(game)) == []


def test_a_card_both_looked_at_and_in_the_deck_breaks_an_invariant():
    game = scenario(player(hand=["business_contacts"]), player(), deck=["mine", "trees", "birds", "fish"])
    pick(game, "Play Business Contacts")
    view, decision = position(game)
    view["players"][0]["keeping"]["kept"].append(view["deck"][0])

    assert problems(view, decision) == [f"'{view['deck'][0]}' is in 2 places: the deck and Player 1's cards kept"]


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
            "the City on phobos_space_haven is not Phobos Space Haven's: its owner has not played the card",
        ),
        (
            "phobos_space_haven",
            "greenery",
            1,
            "the Greenery on phobos_space_haven is not on an Area of Mars that is reserved for nothing",
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


def put_special(view: dict[str, Any], area_id: str, card: str, owner: int) -> None:
    """Writes `card`'s special Tile onto a free Area of the view's board, whatever the rules say."""
    tile = special(area_id, card, owner)
    put(view, area_id, tile["tile"], owner)
    (entry,) = [entry for entry in view["board"] if entry["area"] == area_id]
    entry["tile"]["card"] = card


def test_special_tiles_and_reserved_areas_reached_by_the_rules_break_no_invariant():
    tiles = [city("C3", owner=0), city("E2", owner=1)]
    cards = ["noctis_city", "mohole_area", "industrial_center", "land_claim"]
    holding = player(megacredits=43, production={"energy": 1}, hand=cards)
    game = scenario(holding, player(), tiles=tiles)
    for card, area_id in [("Noctis City", "E3"), ("Mohole Area", "A5")]:
        pick(game, f"Play {card}")
        assert problems(*position(game)) == []
        pick(game, area=area_id)
        assert problems(*position(game)) == []
    pick(game, "Pass")  # Player 2's Turn
    for action, area_id in [("Play Industrial Center", "C4"), ("Play Land Claim", "H1")]:
        pick(game, action)
        assert problems(*position(game)) == []
        pick(game, area=area_id)
        assert problems(*position(game)) == []


@pytest.mark.parametrize(
    ("area_id", "card", "owner", "problem"),
    [
        ("H3", "nuclear_zone", 1, "the Nuclear Zone Tile on H3 belongs to Player 2, who has not played its card"),
        ("A4", "nuclear_zone", 0, "the Nuclear Zone Tile on A4 is not on an Area of Mars that is reserved for nothing"),
        ("E3", "nuclear_zone", 0, "the Nuclear Zone Tile on E3 is not on an Area of Mars that is reserved for nothing"),
    ],
)
def test_a_special_tile_where_the_rules_never_allow_one_breaks_an_invariant(area_id, card, owner, problem):
    view, decision = position(scenario(player(played_cards=["nuclear_zone"]), player()))
    put_special(view, area_id, card, owner)

    assert problems(view, decision) == [problem]


@pytest.mark.parametrize(
    ("area_id", "card", "problem"),
    [
        ("C3", "lava_flows", "the Lava Flows Tile on C3 is not on a volcano"),
        ("C3", "mining_rights", "the Mining Rights Tile on C3 is not on a steel or titanium bonus"),
        (
            "J1",
            "mining_area",
            "the Mining Area Tile on J1 is not on a steel or titanium bonus next to another of its owner's Tiles",
        ),
        ("J1", "industrial_center", "the Industrial Center Tile on J1 is not next to a City"),
    ],
)
def test_a_special_tile_away_from_where_its_card_puts_it_breaks_an_invariant(area_id, card, problem):
    view, decision = position(scenario(player(played_cards=[card]), player()))
    put_special(view, area_id, card, 0)

    assert problems(view, decision) == [problem]


def test_a_tile_on_land_another_player_claimed_breaks_an_invariant():
    game = scenario(player(played_cards=["land_claim"]), player(), land_claim={"area": "H1", "player": 0})
    view, decision = position(game)
    put(view, "H1", "city", 1)

    assert problems(view, decision) == ["the City on H1 belongs to Player 2, but Player 1 claimed the Area"]


def test_a_claim_without_land_claim_breaks_an_invariant():
    view, decision = position(scenario(land_claim={"area": "H1", "player": 1}))

    assert problems(view, decision) == ["H1 is claimed by Player 2, who has not played Land Claim"]


def test_an_area_decision_offering_land_another_player_claimed_breaks_an_invariant():
    game = scenario(player(megacredits=30), player(played_cards=["land_claim"]), land_claim={"area": "H1", "player": 1})
    pick(game, "City")
    view, decision = position(game)
    decision["options"].append(area_option("H1", "city"))

    assert problems(view, decision) == ["the Area Decision for a City offers H1, where it may not go"]


def test_land_claims_area_decision_offering_a_claimed_area_breaks_an_invariant():
    game = scenario(player(megacredits=1, hand=["land_claim"]), player())
    pick(game, "Play Land Claim")
    view, decision = position(game)
    decision["options"] = [option for option in decision["options"] if option["details"]["area"] != "C3"]

    assert problems(view, decision) == ["the Area Decision for Land Claim leaves out C3, where it may go"]


def test_a_special_tiles_area_decision_offering_an_area_its_card_does_not_allow_breaks_an_invariant():
    game = scenario(player(megacredits=18, hand=["lava_flows"]), player())
    pick(game, "Play Lava Flows")
    view, decision = position(game)
    decision["options"].append(area_option("C3", "special", on="volcanoes"))
    decision["options"][-1]["details"]["card"] = "lava_flows"

    assert problems(view, decision) == [
        "the Area Decision for a Lava Flows Tile on a volcano offers C3, where it may not go"
    ]


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


def test_protected_valleys_greenery_on_an_area_reserved_for_oceans_beside_mangroves_breaks_no_invariant():
    game = scenario(player(hand=["mangrove", "protected_valley"]), player(), temperature=4)
    pick(game, "Play Mangrove")
    pick(game, area="E4")
    pick(game, "Play Protected Valley")
    assert problems(*position(game)) == []

    pick(game, area="E5")

    assert problems(*position(game)) == []


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


def test_lava_tube_settlements_city_on_a_volcano_next_to_another_city_breaks_no_invariant():
    holding = player(megacredits=15, hand=["lava_tube_settlement"], production={"energy": 1})
    game = scenario(holding, player(), prelude=True, tiles=[city("D2", owner=1)])
    pick(game, "Play Lava Tube Settlement")
    pick(game, area="D1")
    assert problems(*position(game)) == []

    view, decision = position(game)
    put(view, "C1", "city", 0)  # A second City on a volcano next to D1 and D2: only one may break the rule.
    assert problems(view, decision) == ["the Cities on D1 and D2 are next to each other"]


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


def test_card_actions_used_and_offered_by_the_rules_break_no_invariant():
    game = scenario(player(steel=1, heat=8, played_cards=["space_elevator", "caretaker_contract"]), player())
    pick(game, "Use the action of Space Elevator")

    assert problems(*position(game)) == []


def test_an_action_used_twice_or_not_the_players_own_breaks_an_invariant():
    game = scenario(player(steel=1, heat=8, played_cards=["space_elevator", "caretaker_contract"]), player())
    pick(game, "Use the action of Space Elevator")
    view, decision = position(game)
    use = next(option for option in decision["options"] if option["details"]["type"] == "use_action")
    # Mine has no action, and Space Elevator's is used.
    for card in ("space_elevator", "mine"):
        decision["options"].append({**use, "details": {"type": "use_action", "card": card}})
    view["players"][1]["used_actions"] = ["caretaker_contract"]

    assert problems(view, decision) == [
        "Player 2 has used the action of 'caretaker_contract', which is not a card with an action they played",
        "Player 1 is offered the action of 'space_elevator' again this Generation",
        "Player 1 is offered the action of 'mine', not a card with an action they played",
    ]


def test_an_action_still_used_after_the_production_phase_breaks_an_invariant():
    game = scenario(player(steel=1, played_cards=["space_elevator"]), player(), draft=False)
    pick(game, "Use the action of Space Elevator")
    end_the_action_phase(game)
    view, decision = position(game)
    assert view["phase"] == "research"
    assert problems(view, decision) == []
    view["players"][0]["used_actions"] = ["space_elevator"]

    assert problems(view, decision) == ["in the research phase, Player 1 has used the actions of space_elevator"]


def test_research_outposts_city_next_to_no_other_tile_breaks_no_invariant():
    game = scenario(player(hand=["research_outpost"]), player(), tiles=[city("C3", owner=1)])
    pick(game, "Play Research Outpost")
    assert problems(*position(game)) == []

    pick(game, area="J1")

    assert problems(*position(game)) == []


def test_research_outposts_area_decision_offering_an_area_next_to_a_tile_breaks_an_invariant():
    game = scenario(player(hand=["research_outpost"]), player(), tiles=[city("C3", owner=1)])
    pick(game, "Play Research Outpost")
    view, decision = position(game)
    decision["options"].append(area_option("C2", "city", on="next_to_no_other_tile"))

    assert problems(view, decision) == [
        "the Area Decision for a City next to no other Tile offers C2, where it may not go"
    ]


def test_discounted_costs_and_an_effect_on_the_next_card_reached_by_the_rules_break_no_invariant():
    holding = player(megacredits=20, hand=["indentured_workers", "satellites", "mine"], played_cards=["space_station"])
    game = scenario(holding, player())
    pick(game, "Play Indentured Workers")

    assert problems(*position(game)) == []


def test_a_cost_the_discounts_do_not_leave_breaks_an_invariant():
    game = scenario(player(megacredits=20, hand=["satellites", "mine"], played_cards=["space_station"]), player())
    view, decision = position(game)
    view["players"][0]["card_costs"]["mine"] = 2
    play = next(option for option in decision["options"] if option["details"].get("card") == "satellites")
    play["details"]["cost"] = 10

    assert problems(view, decision) == [
        "Player 1's Mine costs 2, not 4",
        "Play Satellites (8 MegaCredits) is offered at 10, not at 8",
    ]


def test_an_effect_on_the_next_card_that_is_no_such_event_or_outlasts_the_action_phase_breaks_an_invariant():
    game = scenario(player(hand=["mine"], played_cards=["sponsors", "special_design"]), player(), draft=False)
    end_the_action_phase(game)
    view, decision = position(game)
    view["players"][0]["next_card"] = "special_design"
    view["players"][1]["next_card"] = "sponsors"

    assert problems(view, decision) == [
        "in the research phase, Player 1's next card still waits on 'special_design'",
        "Player 2's next card waits on 'sponsors', not an Event with such an effect they played",
        "in the research phase, Player 2's next card still waits on 'sponsors'",
    ]


def test_aquifer_turbines_offering_only_the_areas_that_cover_its_price_breaks_no_invariant():
    game = scenario(player(prelude_cards=["aquifer_turbines"], megacredits=1), player(), prelude=True,
                    tiles=[ocean("E5")])

    assert problems(*position(game)) == []


def test_aquifer_turbines_offering_an_area_that_doesnt_cover_its_price_breaks_an_invariant():
    game = scenario(player(prelude_cards=["aquifer_turbines"], megacredits=1), player(), prelude=True,
                    tiles=[ocean("E5")])
    view, decision = position(game)
    decision["options"].append(area_option("A2", "ocean"))

    assert problems(view, decision) == ["the Area Decision for an Ocean offers A2, where it may not go"]


def test_an_event_played_for_a_prelude_card_may_wait_on_the_next_card_while_players_play_them():
    game = scenario(player(prelude_cards=["excentric_sponsor", "donation"], hand=["special_design", "mine"]),
                    player(), prelude=True)
    pick(game, "Play Excentric Sponsor")
    pick(game, "Play Special Design")

    assert problems(*position(game)) == []


def test_a_prelude_cards_effect_on_the_card_it_plays_reached_by_the_rules_breaks_no_invariant():
    sponsored = scenario(player(prelude_cards=["excentric_sponsor"], hand=["io_mining_industries", "mine"]), player(),
                         prelude=True)
    experts = scenario(player(prelude_cards=["ecology_experts"], hand=["trees"]), player(), prelude=True)

    assert problems(*position(sponsored)) == []
    assert problems(*position(experts)) == []


def test_a_prelude_cards_effect_on_the_card_it_plays_outlasting_its_playing_breaks_an_invariant():
    game = scenario(player(played_prelude_cards=["excentric_sponsor"], hand=["mine"]),
                    player(hand=["trees"]), prelude=True)
    view, decision = position(game)
    view["players"][0]["next_card"] = "excentric_sponsor"
    view["players"][1]["next_card"] = "ecology_experts"

    assert problems(view, decision) == [
        "in the action phase, Player 1's next card still waits on the Prelude Card 'excentric_sponsor'",
        # The costs shown follow what the next card waits on.
        "Player 1's Mine costs 4, not 0",
        "Player 2's next card waits on 'ecology_experts', a Prelude Card they haven't played",
        "in the action phase, Player 2's next card still waits on the Prelude Card 'ecology_experts'",
        "Play Mine (4 MegaCredits) is offered at 4, not at 0",
    ]


def test_mars_universitys_decision_leaving_out_a_card_in_hand_breaks_an_invariant():
    game = scenario(player(megacredits=8, hand=["mars_university", "mine", "trees"]), player())
    pick(game, "Play Mars University")
    view, decision = position(game)
    assert problems(view, decision) == []
    del decision["options"][0]

    assert problems(view, decision) == [
        (
            "Mars University's Decision offers [{'type': 'discard_card', 'card': 'trees'}, {'type': 'done'}], "
            "not every card in the hand and Done"
        )
    ]


def test_a_target_decision_offering_the_players_own_production_while_an_opponent_can_lose_it_breaks_an_invariant():
    game = scenario(
        player(hand=["heat_trappers"], production={"heat": 2}),
        player(production={"heat": 2}),
        player(production={"heat": 3}),
    )
    pick(game, "Play Heat Trappers")
    view, decision = position(game)
    assert problems(view, decision) == []
    decision["options"][1]["details"]["player"] = 0

    assert problems(view, decision) == ["Heat Trappers offers to lower the Production of [1, 0], not of [1, 2]"]


def test_a_target_decision_removing_more_than_the_target_has_or_from_the_player_breaks_an_invariant():
    game = scenario(player(megacredits=1, plants=4, hand=["sabotage"]), player(megacredits=5, steel=9))
    pick(game, "Play Sabotage")
    view, decision = position(game)
    assert problems(view, decision) == []
    decision["options"][0]["details"]["resources"]["steel"] = -9
    decision["options"][1]["details"]["player"] = 0

    assert problems(view, decision) == [
        "Sabotage offers to remove [(1, 'steel', -9), (0, 'megacredits', -5)], "
        "not [(1, 'steel', -4), (1, 'megacredits', -5)]"
    ]


def test_a_target_decision_without_remove_nothing_or_stealing_with_sabotage_breaks_an_invariant():
    game = scenario(player(megacredits=1, hand=["sabotage"]), player(megacredits=5, steel=9))
    pick(game, "Play Sabotage")
    view, decision = position(game)
    decision["options"][0]["details"]["stolen"] = True
    del decision["options"][-1]

    assert problems(view, decision) == [
        "Sabotage offers to remove [(1, 'steel', -4)], not [(1, 'steel', -4), (1, 'megacredits', -5)]",
        "Sabotage's target Decision ends with {'type': 'remove_resources', 'card': 'sabotage', 'player': 1, "
        "'resources': {'megacredits': -5, 'steel': 0, 'titanium': 0, 'plants': 0, 'energy': 0, 'heat': 0}}, "
        "not Remove nothing",
        "Sabotage offers to steal Resources",
    ]


def test_floodings_target_decision_offering_some_opponents_breaks_no_invariant():
    game = scenario(
        player(megacredits=7, hand=["flooding"]),
        player(megacredits=5),
        player(megacredits=5),
        tiles=[city("A1", owner=1), city("J1", owner=2)],
    )
    pick(game, "Play Flooding")
    pick(game, area="A2")

    assert problems(*position(game)) == []


def test_cards_bought_with_inventors_guild_break_no_invariant():
    game = scenario(player(megacredits=3, played_cards=["inventors_guild"]), player(), deck=["mine", "trees"])
    pick(game, "Use the action of Inventors' Guild")

    assert problems(*position(game)) == []


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


def test_positions_with_corporations_reached_by_the_rules_break_no_invariant():
    game = tm_engine.Game(seed=7, players=3)
    for _ in range(80):
        assert problems(*position(game)) == []
        game.play_randomly(seed=1, picks=1)


def test_a_corporation_revealed_at_setup_breaks_an_invariant():
    view, decision = position(tm_engine.Game(seed=7))
    view["players"][0]["corporation"] = "helion"

    assert "at setup, Player 1's Corporation helion is revealed" in problems(view, decision)


def test_a_corporation_being_chosen_after_setup_breaks_an_invariant():
    view, decision = position(scenario(player(), player()))
    view["players"][1]["choosing_corporation"] = {"dealt": ["helion", "thorgate"], "picked": None}

    assert problems(view, decision) == ["in the action phase, Player 2 is choosing a Corporation"]


def test_a_corporation_chosen_that_was_not_dealt_or_dealt_twice_breaks_an_invariant():
    view, decision = position(tm_engine.Game(seed=7))
    choosing = view["players"][0]["choosing_corporation"]
    choosing["picked"] = next(each for each in CORPORATIONS if each not in choosing["dealt"])
    view["players"][1]["choosing_corporation"]["dealt"][0] = choosing["dealt"][0]

    found = problems(view, decision)
    assert f"Player 1 chose {choosing['picked']}, which was not dealt to them" in found
    assert f"{choosing['dealt'][0]} is with 2 Players" in found


def test_a_corporation_decision_offering_another_corporation_breaks_an_invariant():
    game = tm_engine.Game(seed=7)
    view, decision = position(game)
    deciding = view["players"][decision["player"]]["choosing_corporation"]
    other = next(each for each in CORPORATIONS if each not in deciding["dealt"])
    decision["options"][0]["details"]["card"] = other

    offered = [other, deciding["dealt"][1]]
    assert problems(view, decision) == [
        f"Player {decision['player'] + 1} is offered the Corporations {offered}, not those dealt to them"
    ]


def test_a_first_action_on_a_corporation_without_one_or_left_out_breaks_an_invariant():
    view, decision = position(scenario(player(corporation="helion"), player()))
    view["players"][0]["first_action_due"] = True
    assert problems(view, decision)[0] == "Player 1 has a first action due with helion"

    view, decision = position(scenario(player(corporation="inventrix", first_action_due=True), player()))
    decision["options"] = [option for option in decision["options"] if option["details"]["type"] == "pass"]
    assert problems(view, decision) == [
        "Player 1 must take the first action of inventrix first, but is offered ['pass']"
    ]


def test_offering_united_nations_mars_initiatives_action_without_a_raise_breaks_an_invariant():
    game = scenario(player(corporation="united_nations_mars_initiative"), player())
    pick(game, "Asteroid")
    view, decision = position(game)
    view["players"][0]["terraform_rating_raised"] = False

    assert problems(view, decision) == [
        "Player 1 is offered the action of 'united_nations_mars_initiative' without a raise this Generation"
    ]


def test_a_discount_a_corporation_gives_that_is_not_taken_off_breaks_an_invariant():
    view, decision = position(scenario(player(corporation="teractor", hand=["sponsors"]), player()))
    view["players"][0]["card_costs"]["sponsors"] = 6

    assert problems(view, decision) == ["Player 1's Sponsors costs 6, not 3"]


def test_a_standard_project_at_the_wrong_cost_breaks_an_invariant():
    view, decision = position(scenario(player(corporation="thorgate"), player()))
    (power_plant,) = [option for option in decision["options"] if option["details"].get("project") == "power_plant"]
    power_plant["details"]["cost"] = 11

    assert problems(view, decision) == ["Power Plant (8 MegaCredits) is offered at 11, not at 8"]


def test_converting_the_wrong_number_of_plants_breaks_an_invariant():
    view, decision = position(scenario(player(corporation="ecoline", plants=7), player()))
    (convert,) = [option for option in decision["options"] if option["details"]["type"] == "convert_plants"]
    convert["details"]["plants"] = 8

    assert problems(view, decision) == ["Convert 7 plants into a Greenery takes 8 plants, not 7"]


def test_a_discount_per_building_tag_that_is_not_taken_off_breaks_an_invariant():
    game = scenario(player(corporation="cheung_shing_mars", hand=["mine", "sponsors"]), player(), prelude=True)
    view, decision = position(game)
    assert problems(view, decision) == []

    view["players"][0]["card_costs"]["mine"] = 4
    assert problems(view, decision) == ["Player 1's Mine costs 4, not 2"]


def test_a_way_to_pay_with_heat_without_helion_or_that_does_not_cover_the_cost_breaks_an_invariant():
    game = scenario(player(corporation="helion", megacredits=2, heat=5, hand=["sponsors"]), player())
    pick(game, "Play Sponsors")
    view, decision = position(game)
    view["players"][0]["corporation"] = "thorgate"
    view["players"][0]["tags"] |= {"space": 0, "power": 1}

    assert problems(view, decision) == [
        "Pay 2 MegaCredits and 4 heat is offered to Player 1, who may not spend that heat",
        "Pay 1 MegaCredit and 5 heat is offered to Player 1, who may not spend that heat",
    ]

    view, decision = position(game)
    decision["options"][0]["details"]["heat"] = 3
    assert problems(view, decision) == ["Pay 2 MegaCredits and 4 heat is worth 5, but the cost is 6"]


def test_paying_with_the_heat_a_card_loses_breaks_an_invariant():
    game = scenario(player(corporation="helion", megacredits=1, heat=6, hand=["local_heat_trapping"]), player())
    pick(game, "Play Local Heat Trapping")
    view, decision = position(game)
    view["players"][0]["resources"]["heat"] = 5

    assert problems(view, decision) == ["Pay 1 heat is offered to Player 1, who may not spend that heat"]


def test_paying_with_microbes_not_on_psychrophiles_or_for_a_card_without_a_plant_tag_breaks_an_invariant():
    game = scenario(
        player(megacredits=9, hand=["adapted_lichen"], played_cards=["psychrophiles"],
               card_resources={"psychrophiles": 2}),
        player(),
        prelude=True,
    )
    pick(game, "Play Adapted Lichen")
    view, decision = position(game)
    assert problems(view, decision) == []

    view["players"][0]["card_resources"]["psychrophiles"] = 1
    assert problems(view, decision) == [
        "Pay 5 MegaCredits and 2 microbes is offered to Player 1, who has 1 microbes on Psychrophiles"
    ]

    view, decision = position(game)
    decision["options"][2]["details"]["card"] = "mine"
    decision["options"][2]["details"]["megacredits"] = 0
    assert problems(view, decision) == [
        "Pay 5 MegaCredits and 2 microbes pays microbes for Mine, which has no plant Tag",
    ]


def test_tags_that_do_not_count_the_corporation_break_an_invariant():
    view, decision = position(scenario(player(corporation="mining_guild"), player()))
    view["players"][0]["tags"]["building"] = 0

    assert problems(view, decision) == ["Player 1 shows 0 building Tags, but their Corporation has 2"]


def test_robotic_workforce_copying_tharsis_republics_effect_breaks_an_invariant():
    game = scenario(player(corporation="mining_guild", hand=["robotic_workforce"], played_cards=["mine"]), player())
    pick(game, "Play Robotic Workforce")
    view, decision = position(game)
    view["players"][0]["corporation"] = "tharsis_republic"
    view["players"][0]["tags"]["building"] = 1
    decision["options"] = decision["options"][:1]
    decision["options"][0]["details"]["card"] = "tharsis_republic"

    assert problems(view, decision) == [
        "Robotic Workforce offers to copy the production box of Tharsis Republic, not a building card of Player 1's"
    ]


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


def test_positions_with_card_resources_reached_by_the_rules_break_no_invariant():
    game = scenario(
        player(energy=6, played_cards=["physics_complex", "tardigrades"], card_resources={"tardigrades": 7}),
        player(played_cards=["ants"], card_resources={"ants": 1}),
    )

    assert problems(*position(game)) == []


def test_card_resources_on_a_card_that_holds_none_or_too_few_break_an_invariant():
    view, decision = position(scenario(player(played_cards=["tardigrades", "trees"]), player(played_cards=["ants"])))
    view["players"][0]["card_resources"] = {"tardigrades": -1, "trees": 1}
    view["players"][1]["card_resources"] = {}

    assert problems(view, decision) == [
        "Player 1's board shows Card Resources on ['tardigrades', 'trees'], not on ['tardigrades']",
        "Player 1's tardigrades has -1 Card Resources",
        "Player 2's board shows Card Resources on [], not on ['ants']",
    ]


def test_card_resources_count_for_the_card_victory_points_the_board_shows():
    game = scenario(
        player(played_cards=["tardigrades"], card_resources={"tardigrades": 4}), player(), **terraformed_mars()
    )
    end_the_generation(game)
    for _ in range(4):
        if game.is_over:
            break
        pick(game, "Done")
    view, decision = position(game)
    assert problems_at_the_end(view, decision) == []
    view["players"][0]["card_resources"]["tardigrades"] = 8

    assert problems_at_the_end(view, decision) == ["Player 1's score has 1 Victory Point for Cards, but the board gives 2"]


def test_actions_that_cannot_be_carried_out_break_an_invariant():
    game = scenario(
        player(megacredits=1, energy=6, played_cards=["physics_complex", "search_for_life", "ants"]),
        player(played_cards=["tardigrades"], card_resources={"tardigrades": 1}),
    )
    view, decision = position(game)
    assert problems(view, decision) == []
    view["players"][0]["resources"]["energy"] = 5
    view["players"][0]["resources"]["megacredits"] = 0
    view["players"][1]["card_resources"]["tardigrades"] = 0

    assert problems(view, decision) == [
        "Use the action of Search for Life is offered, but Player 1 cannot carry it out",
        "Use the action of Ants is offered, but Player 1 cannot carry it out",
        "Use the action of Physics Complex is offered, but Player 1 cannot carry it out",
    ]


def test_an_add_to_card_decision_offering_a_card_of_the_wrong_kind_or_too_few_breaks_an_invariant():
    game = scenario(
        player(played_cards=["symbiotic_fungus", "tardigrades", "regolith_eaters"]),
        player(),
    )
    pick(game, "Use the action of Symbiotic Fungus")
    view, decision = position(game)
    assert problems(view, decision) == []
    decision["options"][1]["details"]["to"] = "physics_complex"

    assert problems(view, decision) == [
        (
            "Symbiotic Fungus offers to add [('regolith_eaters', 'microbe', 1), ('physics_complex', 'microbe', 1)], "
            "not [('regolith_eaters', 'microbe', 1), ('tardigrades', 'microbe', 1)]"
        )
    ]
    del decision["options"][1]
    assert problems(view, decision)[-1] == "Symbiotic Fungus's add_to_card Decision has 1 Option"


def test_ceos_favorite_project_offering_a_card_with_none_on_it_breaks_an_invariant():
    game = scenario(
        player(
            megacredits=1,
            hand=["ceos_favorite_project"],
            played_cards=["tardigrades", "physics_complex", "ants"],
            card_resources={"tardigrades": 1, "physics_complex": 1},
        ),
        player(),
    )
    pick(game, "Play CEO's Favorite Project")
    view, decision = position(game)
    assert problems(view, decision) == []
    view["players"][0]["card_resources"]["tardigrades"] = 0

    assert problems(view, decision) == [
        (
            "CEO's Favorite Project offers to add [('tardigrades', 'microbe', 1), ('physics_complex', 'science', 1)], "
            "not [('physics_complex', 'science', 1)]"
        )
    ]


def test_an_effects_decision_without_enough_on_the_card_breaks_an_invariant():
    holding = player(played_cards=["regolith_eaters"], card_resources={"regolith_eaters": 2})
    game = scenario(holding, player())
    pick(game, "Use the action of Regolith Eaters")
    view, decision = position(game)
    assert problems(view, decision) == []
    view["players"][0]["card_resources"]["regolith_eaters"] = 1
    del decision["options"][0]

    assert problems(view, decision) == [
        "Regolith Eaters's effects Decision does not offer its 2 alternatives",
        "Regolith Eaters offers to remove 2, but has 1",
    ]


def test_extreme_cold_fungus_offering_microbes_without_a_card_for_them_breaks_an_invariant():
    game = scenario(player(played_cards=["extreme_cold_fungus", "tardigrades"]), player())
    pick(game, "Use the action of Extreme-Cold Fungus")
    view, decision = position(game)
    assert problems(view, decision) == []
    view["players"][0]["played_cards"].remove("tardigrades")
    del view["players"][0]["card_resources"]["tardigrades"]
    view["discard"].append("tardigrades")
    view["discard_size"] += 1

    assert problems(view, decision) == ["Extreme-Cold Fungus offers to add microbes, but Player 1 has no card for them"]


def test_ants_taking_from_its_players_own_card_while_an_opponent_has_some_breaks_an_invariant():
    game = scenario(
        player(played_cards=["ants", "tardigrades"], card_resources={"tardigrades": 3}),
        player(played_cards=["regolith_eaters", "decomposers"], card_resources={"regolith_eaters": 1, "decomposers": 1}),
    )
    pick(game, "Use the action of Ants")
    view, decision = position(game)
    assert problems(view, decision) == []
    decision["options"][0]["details"] |= {"player": 0, "from": "tardigrades"}

    assert problems(view, decision) == [
        "Ants offers to take from [(0, 'tardigrades'), (1, 'decomposers')], not [(1, 'regolith_eaters'), (1, 'decomposers')]"
    ]


def test_predators_taking_from_pets_or_protected_habitats_breaks_an_invariant():
    game = scenario(
        player(played_cards=["predators"]),
        player(played_cards=["fish", "pets"], card_resources={"fish": 1, "pets": 2}),
        player(played_cards=["birds", "protected_habitats"], card_resources={"birds": 1}),
        player(played_cards=["livestock"], card_resources={"livestock": 1}),
    )
    pick(game, "Use the action of Predators")
    view, decision = position(game)
    assert problems(view, decision) == []
    decision["options"][0]["details"] |= {"from": "pets"}
    decision["options"][1]["details"] |= {"player": 2, "from": "birds"}

    assert problems(view, decision) == [
        "Predators offers to take from [(1, 'pets'), (2, 'birds')], not [(1, 'fish'), (3, 'livestock')]"
    ]


def play_protected_habitats(view: dict[str, Any], owner: int) -> None:
    """Moves Protected Habitats from the deck of the view to the played cards of Player `owner`."""
    view["deck"].remove("protected_habitats")
    view["deck_size"] -= 1
    view["players"][owner]["played_cards"].append("protected_habitats")


def test_ants_with_only_a_protected_microbe_to_take_breaks_an_invariant():
    game = scenario(
        player(played_cards=["ants", "tardigrades"], card_resources={"ants": 1}),
        player(played_cards=["decomposers"], card_resources={"decomposers": 3}),
    )
    view, decision = position(game)
    assert problems(view, decision) == []
    view["players"][0]["card_resources"]["ants"] = 0
    play_protected_habitats(view, 1)

    assert problems(view, decision) == ["Use the action of Ants is offered, but Player 1 cannot carry it out"]


def test_security_fleet_and_predators_with_nothing_to_spend_break_an_invariant():
    game = scenario(
        player(titanium=1, played_cards=["security_fleet", "predators"]),
        player(played_cards=["pets", "fish"], card_resources={"fish": 1}),
    )
    view, decision = position(game)
    assert problems(view, decision) == []
    view["players"][0]["resources"]["titanium"] = 0
    view["players"][1]["card_resources"]["fish"] = 0
    view["players"][1]["card_resources"]["pets"] = 3

    assert problems(view, decision) == [
        "Use the action of Predators is offered, but Player 1 cannot carry it out",
        "Use the action of Security Fleet is offered, but Player 1 cannot carry it out",
    ]


def test_virus_offering_a_protected_players_plants_or_animals_or_too_many_breaks_an_invariant():
    game = scenario(
        player(megacredits=1, hand=["virus"]),
        player(plants=9, played_cards=["fish"], card_resources={"fish": 1}),
        player(plants=2, played_cards=["birds"], card_resources={"birds": 5}),
    )
    pick(game, "Play Virus")
    view, decision = position(game)
    assert problems(view, decision) == []
    decision["options"][2]["details"]["amount"] = 5
    play_protected_habitats(view, 1)

    assert problems(view, decision) == [
        (
            "Virus offers to remove [(1, 'fish', -1), (1, 'plants', -5), (2, 'birds', -5), (2, 'plants', -2)], "
            "not [(2, 'birds', -2), (2, 'plants', -2)]"
        )
    ]


def test_asteroid_offering_a_protected_players_plants_breaks_an_invariant():
    game = scenario(
        player(megacredits=14, hand=["asteroid"]),
        player(plants=9),
        player(plants=2),
    )
    pick(game, "Play Asteroid")
    view, decision = position(game)
    assert problems(view, decision) == []
    play_protected_habitats(view, 1)

    assert problems(view, decision) == [
        "Asteroid offers to remove [(1, 'plants', -3), (2, 'plants', -2)], not [(2, 'plants', -2)]"
    ]


def test_a_card_played_offering_the_wrong_alternatives_breaks_an_invariant():
    game = scenario(
        player(megacredits=1, heat=5, hand=["local_heat_trapping"], played_cards=["fish"]),
        player(),
    )
    pick(game, "Play Local Heat Trapping")
    view, decision = position(game)
    assert problems(view, decision) == []
    decision["options"][1]["details"]["alternative"] = 2

    assert problems(view, decision) == ["Local Heat Trapping offers the alternatives [0, 2], not [0, 1]"]
    del decision["options"][1]
    assert problems(view, decision) == [
        "Local Heat Trapping offers the alternatives [0], not [0, 1]",
        "Local Heat Trapping's effects Decision has 1 Option",
    ]


def test_imported_nitrogen_adding_an_amount_not_printed_breaks_an_invariant():
    game = scenario(
        player(megacredits=23, hand=["imported_nitrogen"], played_cards=["tardigrades", "fish", "birds"]),
        player(),
    )
    pick(game, "Play Imported Nitrogen")
    view, decision = position(game)
    assert decision["kind"] == "add_to_card"
    assert problems(view, decision) == []
    decision["options"][0]["details"]["amount"] = 3

    assert problems(view, decision) == [
        (
            "Imported Nitrogen offers to add [('fish', 'animal', 3), ('birds', 'animal', 2)], "
            "not [('fish', 'animal', 2), ('birds', 'animal', 2)]"
        )
    ]


def test_viral_enhancers_asking_about_a_card_that_holds_nothing_breaks_an_invariant():
    game = scenario(player(megacredits=4, hand=["tardigrades"], played_cards=["viral_enhancers"]), player())
    pick(game, "Play Tardigrades")
    view, decision = position(game)
    assert decision["kind"] == "viral_enhancers"
    assert problems(view, decision) == []
    for option in decision["options"]:
        option["details"]["card"] = "mine"

    assert problems(view, decision) == [
        "Viral Enhancers asks about 'mine', not a card of Player 1's that holds Card Resources",
        "Viral Enhancers asks about Mine, which has no plant, microbe or animal Tag",
    ]


def test_ecological_zones_tile_not_next_to_a_greenery_breaks_an_invariant():
    game = scenario(
        player(played_cards=["ecological_zone"]),
        player(),
        tiles=[greenery("C3", owner=0), special("C4", "ecological_zone", owner=0)],
    )
    view, decision = position(game)
    assert problems(view, decision) == []
    next(entry for entry in view["board"] if entry["area"] == "C3")["tile"] = None

    assert problems(view, decision) == ["the Ecological Zone Tile on C4 is not next to a Greenery"]


def test_an_olympus_conference_decision_without_a_science_or_its_options_breaks_an_invariant():
    game = scenario(
        player(
            megacredits=13,
            hand=["regolith_eaters", "mine"],
            played_cards=["mars_university", "olympus_conference"],
            card_resources={"olympus_conference": 1},
        ),
        player(),
    )
    pick(game, "Play Regolith Eaters")
    view, decision = position(game)
    assert problems(view, decision) == []
    view["players"][0]["card_resources"]["olympus_conference"] = 0
    del decision["options"][2]

    assert problems(view, decision) == [
        "Olympus Conference offers to remove a science, but has none",
        "Olympus Conference's Decision also offers [{'type': 'done'}], not every card in the hand and Done",
    ]


def test_positions_with_prelude_reached_by_the_rules_break_no_invariant():
    game = tm_engine.Game(seed=7, players=3, prelude=True)
    phases = set()
    for _ in range(80):
        assert problems(*position(game)) == []
        phases.add(game.full_view()["phase"])
        game.play_randomly(seed=1, picks=1)
    assert {"setup", "prelude_cards", "action"} <= phases


def test_prelude_cards_without_prelude_break_an_invariant():
    view, decision = position(scenario(player(), player()))
    view["players"][0]["played_prelude_cards"] = ["donation"]

    assert problems(view, decision) == ["without Prelude, Player 1 has Prelude Cards"]


def test_prelude_cards_dealt_twice_or_kept_without_being_dealt_break_an_invariant():
    view, decision = position(tm_engine.Game(seed=7, prelude=True))
    first, second = view["players"][0]["prelude_cards"], view["players"][1]["prelude_cards"]
    second["dealt"][0] = first["dealt"][0]
    kept = next(card for card in PRELUDE_CARDS if card not in first["dealt"])
    first["kept"] = [kept]

    found = problems(view, decision)
    assert f"the Prelude Card {first['dealt'][0]} is in 2 places" in found
    assert f"at setup, Player 1 was dealt {first['dealt']} and kept {[kept]}" in found


def test_prelude_cards_still_held_in_the_action_phase_break_an_invariant():
    view, decision = position(scenario(player(), player(), prelude=True))
    view["players"][0]["prelude_cards"] = {"dealt": [], "kept": ["donation"]}

    assert problems(view, decision) == ["in the action phase, Player 1 has ['donation'] still to play"]


def test_more_than_two_prelude_cards_played_breaks_an_invariant():
    three_played = player(played_prelude_cards=["donation", "loan", "mohole"])
    view, decision = position(scenario(three_played, player(), prelude=True))

    assert problems(view, decision) == [
        "Player 1 has [] still to play and ['donation', 'loan', 'mohole'] played, more than 2"
    ]


def test_valley_trusts_first_action_reached_by_the_rules_breaks_no_invariant():
    valley_trust = player(corporation="valley_trust", first_action_due=True, played_prelude_cards=["donation", "loan"],
                          hand=["trees"], megacredits=13)
    game = scenario(valley_trust, player(), prelude=True, prelude_deck=["ecology_experts", "mohole", "supplier"])
    pick(game, "First action")
    assert problems(*position(game)) == []

    pick(game, "Play Ecology Experts")
    assert problems(*position(game)) == []
    pick(game, "Play Trees")
    assert problems(*position(game)) == []


def test_four_prelude_cards_played_with_valley_trust_breaks_an_invariant():
    four_played = player(corporation="valley_trust", played_prelude_cards=["donation", "loan", "mohole", "supplier"])
    view, decision = position(scenario(four_played, player(), prelude=True))

    assert problems(view, decision) == [
        "Player 1 has [] still to play and ['donation', 'loan', 'mohole', 'supplier'] played, more than 3"
    ]


def test_a_prelude_card_decision_offering_one_not_kept_breaks_an_invariant():
    view, decision = position(scenario(player(prelude_cards=["donation", "loan"]), player(), prelude=True))
    decision["options"][1]["details"]["card"] = "mohole"

    assert problems(view, decision) == [
        "Player 1 is offered the Prelude Cards ['donation', 'mohole'], not ['donation', 'loan']"
    ]
