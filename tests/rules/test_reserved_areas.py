"""Areas reserved for a card's Tile: Noctis City's on Mars, and Phobos Space Haven's and Ganymede
Colony's off Mars. Each takes only its card's City, and an Area claimed with Land Claim takes only
its Player's Tiles."""

import pytest
import tm_engine

from tests.helpers import (
    CARD_NAMES,
    RESERVED_FOR_CARDS,
    areas_offered,
    city,
    greenery,
    ocean,
    pick,
    play_randomly,
    player,
    scenario,
)

# Each reserved Area, by the card whose City it is kept for.
RESERVED_AREAS = {card: area_id for area_id, card in RESERVED_FOR_CARDS.items()}

# Every card in this hand places a Tile by a placement rule of its own, and the Scenario lets each be
# played: Oceans for Capital, a Temperature for Mangrove and Artificial Lake, two Cities with C4
# between them for Urbanized Area and Industrial Center, and a Greenery on H5, next to H6's titanium
# bonus, for Mining Area.
PLACING_CARDS = [
    "capital",
    "natural_preserve",
    "mining_area",
    "mining_rights",
    "commercial_district",
    "nuclear_zone",
    "industrial_center",
    "ecological_zone",
    "urbanized_area",
    "mangrove",
    "lava_flows",
    "mohole_area",
    "artificial_lake",
    "research_outpost",
    "restricted_area",
]
RICH = player(megacredits=200, plants=8, production={"energy": 3}, hand=PLACING_CARDS)
TILES = [ocean(name) for name in ("A2", "A4", "A5", "B6")] + [
    city("C3", owner=1),
    city("C5", owner=0),
    greenery("H5", owner=0),
]


@pytest.mark.parametrize(
    "action",
    [
        "City (25 MegaCredits)",
        "Greenery (23 MegaCredits)",
        "Aquifer (18 MegaCredits)",
        "Convert 8 plants into a Greenery",
        *(f"Play {CARD_NAMES[card]}" for card in PLACING_CARDS),
    ],
)
def test_no_other_tile_goes_on_a_reserved_area(action):
    game = scenario(RICH, player(), temperature=4, tiles=TILES)

    pick(game, action)
    if game.decision["kind"] == "payment":
        pick(game, game.decision["options"][0]["label"])

    assert game.decision["kind"] == "area"
    assert not set(areas_offered(game)) & set(RESERVED_AREAS.values())


@pytest.mark.parametrize("card", RESERVED_AREAS)
def test_each_reserved_areas_card_places_its_city_there_and_nowhere_else(card):
    game = scenario(
        player(megacredits=30, production={"energy": 1}, hand=[card]), player()
    )

    pick(game, f"Play {card.replace('_', ' ').title()}")

    assert areas_offered(game) == [RESERVED_AREAS[card]]


def test_in_random_games_each_reserved_area_holds_only_its_cards_city_and_a_claimed_area_only_its_players_tiles():
    used = {card: 0 for card in RESERVED_AREAS} | {"land_claim": 0}
    for seed in range(40):
        game = tm_engine.Game(
            seed=seed, players=2 + seed % 4, implemented_cards_first=True
        )
        play_randomly(game, seed=seed)
        view = game.full_view()
        played = [set(each["played_cards"]) for each in view["players"]]
        for area in view["board"]:
            tile = area["tile"]
            if area["claimed_by"] is not None:
                used["land_claim"] += 1
                assert "land_claim" in played[area["claimed_by"]], (seed, area)
                assert tile is None or tile["owner"] in (None, area["claimed_by"]), (
                    seed,
                    area,
                )
            if tile is None or area["reserved"] in (None, "ocean"):
                continue
            card = area["reserved"]
            used[card] += 1
            assert tile["type"] == "city" and "card" not in tile, (seed, area)
            assert card in played[tile["owner"]], (seed, area)
    # Every reserved Area, and Land Claim, was used in some of these Games.
    assert all(used.values()), used
