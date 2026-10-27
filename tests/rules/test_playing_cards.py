"""Playing a Project Card from the hand: an Action, offered for each card whose Requirements
are met, that the Player can pay for, and whose effects they can carry out."""

import tm_engine

from tests.helpers import (
    LAND_AREAS,
    city,
    final_scores,
    greenery,
    offered,
    options,
    pick,
    player,
    scenario,
    terraformed_mars,
)


def test_each_playable_card_in_hand_is_an_option_naming_the_card_and_its_cost_in_card_number_order():
    game = scenario(player(hand=["trees", "mine"]), player(), temperature=-4)

    found = [option for option in options(game) if option["details"]["type"] == "play_card"]

    assert [(option["label"], option["details"]) for option in found] == [
        ("Play Mine (4 MegaCredits)", {"type": "play_card", "card": "mine", "cost": 4}),
        ("Play Trees (13 MegaCredits)", {"type": "play_card", "card": "trees", "cost": 13}),
    ]


def test_a_card_that_is_not_implemented_yet_is_never_offered():
    # Birds (Active, animals) comes with ticket 20.
    game = scenario(player(megacredits=100, hand=["birds"]), player(), oxygen=13)

    assert not offered(game, "Play Birds")


def test_a_card_is_not_offered_without_the_megacredits_to_pay_for_it():
    assert not offered(scenario(player(megacredits=3, hand=["mine"]), player()), "Play Mine")
    assert offered(scenario(player(megacredits=4, hand=["mine"]), player()), "Play Mine")


def test_a_player_plays_only_their_own_cards_on_their_own_turn():
    game = scenario(player(hand=[]), player(hand=["mine"]))
    assert not offered(game, "Play Mine")

    pick(game, "Pass")

    assert game.decision["player"] == 1
    assert offered(game, "Play Mine")


def test_playing_a_card_is_one_of_the_two_actions_of_a_turn():
    game = scenario(player(hand=["mine", "power_plant"]), player())

    pick(game, "Play Mine")
    assert game.player_view(0)["actions_this_turn"] == 1
    assert game.decision["player"] == 0

    pick(game, "Play Power Plant")
    assert game.decision["player"] == 1


def test_victory_points_on_played_cards_add_up_and_cards_in_hand_score_nothing():
    game = scenario(
        player(played_cards=["trees", "lake_marineris", "solar_power"], hand=["windmills"]),
        player(hand=["dust_seals"]),
        **terraformed_mars(),
    )

    assert [score["cards"] for score in final_scores(game)] == [4, 0]


def test_a_card_with_a_city_tile_is_not_offered_without_an_area_for_the_city():
    # A1 is next to A2 (reserved for Oceans), B1 and B2; every other free Area holds a Greenery.
    every_other_area_taken = [greenery(name, owner=1) for name in LAND_AREAS if name not in ("A1", "B1")]
    holding_domed_crater = player(hand=["domed_crater"], production={"energy": 1})
    a1_free = scenario(holding_domed_crater, player(), tiles=[*every_other_area_taken, greenery("B1", owner=1)])
    a1_next_to_a_city = scenario(holding_domed_crater, player(), tiles=[*every_other_area_taken, city("B1", owner=1)])

    assert offered(a1_free, "Play Domed Crater")
    assert not offered(a1_next_to_a_city, "Play Domed Crater")


def test_no_card_places_two_cities_or_two_greeneries_so_one_area_for_each_is_enough():
    # A card is offered once there is an Area for each of its Tiles on its own, so two Cities
    # would need a check for two Areas.
    for card in tm_engine.card_catalog():
        placements = card.get("effects", {}).get("tiles", [])
        kinds = [placement if isinstance(placement, str) else placement["tile"] for placement in placements]
        assert kinds.count("city") <= 1 and kinds.count("greenery") <= 1, card["id"]
