"""Interplanetary Cinematics (building Tag): Effect: each time you play an Event, you gain 2
MegaCredits. You start with 20 steel and 30 MegaCredits."""

from tests.helpers import (
    pick,
    player,
    player_board,
    production,
    resources,
    scenario,
    start_as,
)


def test_interplanetary_cinematics_starts_with_20_steel_30_megacredits_and_a_building_tag():
    game, first = start_as("interplanetary_cinematics")

    assert resources(game, first) == {
        "megacredits": 30,
        "steel": 20,
        "titanium": 0,
        "plants": 0,
        "energy": 0,
        "heat": 0,
    }
    assert set(production(game, first).values()) == {0}
    assert player_board(game, first)["tags"]["building"] == 1


def test_playing_an_event_gains_2_megacredits_after_paying_for_it():
    game = scenario(
        player(
            corporation="interplanetary_cinematics", megacredits=14, hand=["asteroid"]
        ),
        player(),
    )

    pick(game, "Play Asteroid")

    assert resources(game, 0)["megacredits"] == 2


def test_playing_another_card_gains_nothing():
    game = scenario(
        player(
            corporation="interplanetary_cinematics", megacredits=6, hand=["sponsors"]
        ),
        player(),
    )

    pick(game, "Play Sponsors")

    assert resources(game, 0)["megacredits"] == 0


def test_another_players_event_gains_nothing():
    game = scenario(
        player(megacredits=14, hand=["asteroid"]),
        player(corporation="interplanetary_cinematics"),
    )

    pick(game, "Play Asteroid")

    assert resources(game, 1)["megacredits"] == 42
