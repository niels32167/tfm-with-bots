"""#128 Ecological Zone (12 MegaCredits, plant and animal Tags): Effect: when you play an animal or plant
Tag, including these, add an animal to this card. Requires that you have a Greenery Tile. Place this
Tile adjacent to any Greenery Tile. 1 Victory Point per 2 animals on this card."""

from tests.helpers import (
    ADJACENT_AREAS,
    LAND_AREAS,
    area,
    areas_offered,
    card_resources,
    final_scores,
    greenery,
    ocean,
    offered,
    pick,
    player,
    scenario,
    special,
    terraformed_mars,
)


def hand(**fields):
    return player(megacredits=12, hand=["ecological_zone"], **fields)


def test_it_requires_a_greenery_of_the_players_own():
    assert not offered(scenario(hand(), player()), "Play Ecological Zone")
    assert not offered(
        scenario(hand(), player(), tiles=[greenery("C3", 1)]), "Play Ecological Zone"
    )
    assert offered(
        scenario(hand(), player(), tiles=[greenery("C3", 0)]), "Play Ecological Zone"
    )


def test_its_tile_goes_next_to_any_greenery_whoever_owns_it():
    tiles = [greenery("C3", 0), greenery("G4", 1)]
    game = scenario(hand(), player(), tiles=tiles)

    pick(game, "Play Ecological Zone (12 MegaCredits)")

    assert game.decision["kind"] == "area"
    wanted = {
        name
        for name in LAND_AREAS
        if name not in ("C3", "G4") and ({"C3", "G4"} & set(ADJACENT_AREAS[name]))
    }
    assert set(areas_offered(game)) == wanted
    assert game.decision["options"][0]["details"]["on"] == "next_to_a_greenery"
    assert "Place the Ecological Zone Tile on" in game.decision["options"][0]["label"]


def test_its_tile_is_printed_with_its_symbol_and_belongs_to_its_player():
    game = scenario(hand(), player(), tiles=[greenery("C3", 0)])

    pick(game, "Play Ecological Zone")
    pick(game, area="C4")

    assert area(game, "C4")["tile"] == {
        "type": "special",
        "owner": 0,
        "card": "ecological_zone",
    }


def test_it_is_not_offered_with_no_free_area_next_to_a_greenery():
    # A1 has only A2, B1 and B2 next to it.
    occupied = [greenery("A1", 0)] + [
        special(name, "commercial_district", owner=1) for name in ("B1", "B2")
    ]
    occupied.append(ocean("A2"))

    assert not offered(
        scenario(hand(), player(), tiles=occupied), "Play Ecological Zone"
    )


def test_its_own_two_tags_add_2_animals():
    game = scenario(hand(), player(), tiles=[greenery("C3", 0)])

    pick(game, "Play Ecological Zone")

    assert card_resources(game, 0) == {"ecological_zone": 2}
    assert "Player 1 adds 2 animals to Ecological Zone." in game.log


def test_an_animal_or_plant_tag_adds_an_animal():
    for card, label in (("trees", "Play Trees"), ("pets", "Play Pets")):
        playing = player(megacredits=30, hand=[card], played_cards=["ecological_zone"])
        game = scenario(playing, player(), temperature=8)

        pick(game, label)

        assert card_resources(game, 0)["ecological_zone"] == 1, card


def test_other_tags_and_other_players_tags_add_nothing():
    game = scenario(
        player(megacredits=4, hand=["mine"], played_cards=["ecological_zone"]),
        player(megacredits=13, hand=["trees"]),
        temperature=-4,
    )

    pick(game, "Play Mine")
    pick(game, "End Turn")
    pick(game, "Play Trees")

    assert card_resources(game, 0) == {"ecological_zone": 0}


def test_decomposers_counts_an_animal_tag_on_a_real_animal_card():
    playing = player(megacredits=10, hand=["pets"], played_cards=["decomposers"])
    game = scenario(playing, player())

    pick(game, "Play Pets")

    assert card_resources(game, 0)["decomposers"] == 1


def test_ecological_zone_scores_1_victory_point_per_2_animals():
    for animals, points in ((1, 0), (2, 1), (7, 3)):
        holding = player(
            played_cards=["ecological_zone"],
            card_resources={"ecological_zone": animals},
        )

        game = scenario(holding, player(), **terraformed_mars())
        assert final_scores(game)[0]["cards"] == points
