"""Triggers: what an Active card's Player gains each time something happens while it is in play
(see "Triggers" in docs/rules-notes.md). They fire for the card's own Player, whoever set them
off, once for each Tile, card or Tag that sets them off, including the card being played."""

import tm_engine

from tests.helpers import offered, pick, player, production, resources, scenario

CATALOG = {card["id"]: card for card in tm_engine.card_catalog()}
CARDS_WITH_A_TRIGGER = [card for card in CATALOG.values() if card.get("effects", {}).get("when")]


def test_a_trigger_fires_for_its_cards_player_not_for_the_player_who_sets_it_off():
    game = scenario(player(megacredits=25), player(megacredits=0, played_cards=["rover_construction"]))

    pick(game, "City (25 MegaCredits)")
    pick(game, "Place the City on C3")

    assert resources(game, 1)["megacredits"] == 2
    assert resources(game, 0)["megacredits"] == 0
    assert "Player 2's Rover Construction takes effect." in game.log


def test_a_trigger_fires_once_for_each_tile_that_sets_it_off():
    game = scenario(player(megacredits=23, hand=["ice_asteroid"]), player(played_cards=["arctic_algae"]))

    pick(game, "Play Ice Asteroid")
    pick(game, "Place the Ocean on A4")
    assert resources(game, 1)["plants"] == 2
    pick(game, "Place the Ocean on A5")

    assert resources(game, 1)["plants"] == 4
    assert game.log.count("Player 2's Arctic Algae takes effect.") == 2


def test_the_ocean_a_temperature_step_gives_sets_off_arctic_algae_too():
    game = scenario(player(megacredits=14), player(played_cards=["arctic_algae"]), temperature=-2)

    pick(game, "Asteroid")
    pick(game, "Place the Ocean on A4")

    assert resources(game, 1)["plants"] == 2


def test_every_players_trigger_on_the_same_tile_fires_once():
    holding = player(megacredits=25, played_cards=["rover_construction"])
    game = scenario(holding, player(played_cards=["immigrant_city"]), tiles=[])

    pick(game, "City (25 MegaCredits)")
    pick(game, "Place the City on C3")

    assert resources(game, 0)["megacredits"] == 2
    assert production(game, 1)["megacredits"] == 1
    assert game.log.count("Player 1's Rover Construction takes effect.") == 1
    assert game.log.count("Player 2's Immigrant City takes effect.") == 1


def test_a_card_played_sets_off_its_own_trigger_when_it_matches_immigrant_citys_own_city():
    holding = player(
        megacredits=13, hand=["immigrant_city"], production={"energy": 1}, played_cards=["rover_construction"]
    )
    game = scenario(holding, player())

    pick(game, "Play Immigrant City")
    pick(game, "Place the City on C3")

    assert game.log.count("Player 1's Immigrant City takes effect.") == 1
    assert game.log.count("Player 1's Rover Construction takes effect.") == 1
    assert production(game, 0)["megacredits"] == -1


def test_a_card_played_sets_off_its_own_trigger_when_it_matches_mars_universitys_own_science_tag():
    game = scenario(player(megacredits=8, hand=["mars_university", "mine"]), player())

    pick(game, "Play Mars University")

    assert game.decision["kind"] == "discard_to_draw"


def test_the_card_played_sets_off_the_other_triggers_it_matches():
    # Imported GHG is an Event with space and Earth Tags.
    played = ["media_group", "optimal_aerobraking", "mars_university"]
    game = scenario(player(megacredits=7, hand=["imported_ghg"], played_cards=played), player())

    pick(game, "Play Imported GHG")

    assert resources(game, 0)["megacredits"] == 6
    assert resources(game, 0)["heat"] == 6
    assert game.decision["kind"] == "action"


def test_research_counts_as_two_science_tags_played_so_mars_university_fires_twice():
    holding = player(megacredits=11, hand=["research"], played_cards=["mars_university"])
    game = scenario(holding, player(), deck=["sponsors", "satellites", "lichen", "bushes"])

    pick(game, "Play Research")
    pick(game, "Done")
    assert game.decision["kind"] == "discard_to_draw"
    pick(game, "Done")

    assert offered(game, "End Turn")


def test_only_active_cards_have_a_trigger_and_one_that_its_own_play_sets_off_says_so():
    # A card's Tags and Tiles set off its own Trigger once it is in play, so only cards printed
    # "including this" may match themselves.
    for card in CARDS_WITH_A_TRIGGER:
        assert card["type"] == "active", card["name"]
        effects = card["effects"]
        for trigger in effects["when"]:
            on = trigger["on"]
            own_tile = (
                isinstance(on, dict) and "tile_placed" in on and on["tile_placed"]["tile"] in effects.get("tiles", [])
            )
            own_tag = isinstance(on, dict) and set(on.get("tag_played", [])) & set(card["tags"])
            if own_tile or own_tag:
                assert "including this" in card["text"] or "including these" in card["text"], card["name"]
            if isinstance(on, dict) and "card_played" in on:
                wanted = on["card_played"]
                assert wanted.get("type", card["type"]) != card["type"] or wanted.get("tag") not in card["tags"]
