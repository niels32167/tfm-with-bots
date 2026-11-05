"""PhoboLog (space Tag): Effect: your titanium resources are each worth 1 MegaCredit extra. You start
with 10 titanium and 23 MegaCredits."""

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


def test_phobolog_starts_with_10_titanium_23_megacredits_and_a_space_tag():
    game, first = start_as("phobolog")

    assert resources(game, first) == {
        "megacredits": 23,
        "steel": 0,
        "titanium": 10,
        "plants": 0,
        "energy": 0,
        "heat": 0,
    }
    assert set(production(game, first).values()) == {0}
    assert player_board(game, first)["tags"]["space"] == 1


def test_each_titanium_pays_4_megacredits_towards_a_card_with_a_space_tag():
    game = scenario(
        player(
            corporation="phobolog", megacredits=0, titanium=3, hand=["miranda_resort"]
        ),
        player(),
    )

    assert offered(game, "Play Miranda Resort")
    pick(game, "Play Miranda Resort")

    assert resources(game, 0)["titanium"] == 0
    assert "Player 1 plays Miranda Resort, paying 3 titanium." in game.log


def test_titanium_is_worth_the_usual_3_megacredits_to_another_player():
    game = scenario(
        player(megacredits=0, titanium=3, hand=["miranda_resort"]),
        player(corporation="phobolog"),
    )

    assert not offered(game, "Play Miranda Resort")
