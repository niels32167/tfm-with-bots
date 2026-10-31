"""#020 Research Outpost (18 MegaCredits, building, city and science Tags): Effect: when you play a
card, you pay 1 MegaCredit less for it. Place a City Tile NEXT TO NO OTHER TILE."""

from tests.helpers import (
    ADJACENT_AREAS,
    LAND_AREAS,
    area,
    areas_offered,
    city,
    final_scores,
    greenery,
    ocean,
    offered,
    pick,
    player,
    resources,
    scenario,
    terraformed_mars,
)


def test_research_outpost_has_no_requirements_and_places_a_city_next_to_no_other_tile():
    tiles = [greenery("C3", owner=1), ocean("A2")]
    game = scenario(player(megacredits=18, hand=["research_outpost"]), player(), tiles=tiles)

    pick(game, "Play Research Outpost (18 MegaCredits)")

    next_to_a_tile = {*ADJACENT_AREAS["C3"], *ADJACENT_AREAS["A2"]}
    assert areas_offered(game) == [name for name in LAND_AREAS if name not in next_to_a_tile and name != "C3"]
    assert offered(game, area="J1", on="next_to_no_other_tile")
    pick(game, area="J1")
    assert area(game, "J1")["tile"] == {"type": "city", "owner": 0}
    assert resources(game, 0)["megacredits"] == 0


def test_research_outpost_is_not_offered_without_free_land_next_to_no_other_tile():
    # J1's neighbours are H1, H2 and J2, all land.
    everywhere_but_j1 = [greenery(name, owner=1) for name in LAND_AREAS if name != "J1"]
    around_j1_free = [tile for tile in everywhere_but_j1 if tile["area"] not in ADJACENT_AREAS["J1"]]

    assert not offered(scenario(player(hand=["research_outpost"]), player(), tiles=everywhere_but_j1), "Play Research")
    assert offered(scenario(player(hand=["research_outpost"]), player(), tiles=around_j1_free), "Play Research")


def test_with_research_outpost_every_card_costs_1_megacredit_less():
    game = scenario(player(megacredits=3, hand=["mine", "space_elevator"], played_cards=["research_outpost"]), player())

    assert offered(game, "Play Mine (3 MegaCredits)", type="play_card", card="mine", cost=3)
    pick(game, "Play Mine")
    assert resources(game, 0)["megacredits"] == 0
    assert "Player 1 plays Mine, paying 3 MegaCredits." in game.log


def test_research_outpost_does_not_make_itself_cheaper():
    assert not offered(scenario(player(megacredits=17, hand=["research_outpost"]), player()), "Play Research Outpost")


def test_research_outpost_is_worth_no_victory_points():
    game = scenario(player(played_cards=["research_outpost"]), player(), **terraformed_mars(tiles=[city("J1", 0)]))

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
