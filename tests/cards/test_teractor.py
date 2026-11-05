"""Teractor (Corporate Era, Earth Tag): Effect: when playing an Earth card, you pay 3 MegaCredits
less for it. You start with 60 MegaCredits."""

from tests.helpers import (
    offered,
    pick,
    player,
    player_board,
    production,
    resources,
    scenario,
    start_as,
)


def test_teractor_starts_with_60_megacredits_and_an_earth_tag():
    game, first = start_as("teractor")

    assert resources(game, first) == {
        "megacredits": 60,
        "steel": 0,
        "titanium": 0,
        "plants": 0,
        "energy": 0,
        "heat": 0,
    }
    assert set(production(game, first).values()) == {0}
    assert player_board(game, first)["tags"]["earth"] == 1


def test_a_card_with_an_earth_tag_costs_3_megacredits_less_and_others_do_not():
    game = scenario(
        player(corporation="teractor", megacredits=3, hand=["sponsors", "satellites"]),
        player(),
    )

    assert offered(game, "Play Sponsors (3 MegaCredits)", cost=3)
    assert not offered(game, "Play Satellites")
    pick(game, "Play Sponsors")
    assert resources(game, 0)["megacredits"] == 0


def test_teractors_discount_is_only_for_its_own_player():
    game = scenario(player(hand=["sponsors"]), player(corporation="teractor"))

    assert offered(game, "Play Sponsors (6 MegaCredits)", cost=6)
