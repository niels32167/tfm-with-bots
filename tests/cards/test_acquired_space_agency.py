"""#P35 Acquired Space Agency (Prelude Card): gain 6 titanium. Reveal cards until you reveal two cards with space
Tags. Take them into your hand, discard the rest."""

from tests.helpers import (
    everything_but,
    hand,
    player,
    resources,
    scenario,
)


def test_acquired_space_agency_gains_6_titanium_and_takes_the_first_2_cards_with_a_space_tag_revealed():
    game = scenario(
        player(prelude_cards=["acquired_space_agency"]),
        player(),
        prelude=True,
        deck=["mine", "asteroid", "trees", "satellites", "birds"],
    )

    assert resources(game, 0)["titanium"] == 6
    assert hand(game, 0) == ["asteroid", "satellites"]
    view = game.full_view()
    assert view["discard"] == ["mine", "trees"]
    assert view["deck"][:1] == ["birds"]
    revealed = [line for line in game.log if " reveals " in line]
    assert revealed == [
        "Player 1 reveals Mine and discards it.",
        "Player 1 reveals Asteroid, which has a space Tag, and takes it into their hand.",
        "Player 1 reveals Trees and discards it.",
        "Player 1 reveals Satellites, which has a space Tag, and takes it into their hand.",
    ]



def test_when_the_deck_runs_out_the_discard_pile_is_shuffled_in_but_not_the_cards_just_revealed():
    game = scenario(
        player(prelude_cards=["acquired_space_agency"]),
        player(hand=everything_but("mine", "asteroid", "trees", "comet")),
        prelude=True,
        deck=["mine", "asteroid"],
        discard=["trees", "comet"],
    )

    assert hand(game, 0) == ["asteroid", "comet"]
    view = game.full_view()
    assert sorted(view["discard"]) == ["mine", "trees"]
    assert view["deck"] == []


def test_with_fewer_than_2_cards_with_a_space_tag_left_it_takes_those_there_are():
    game = scenario(
        player(prelude_cards=["acquired_space_agency"]),
        player(hand=everything_but("mine", "asteroid")),
        prelude=True,
        deck=["mine", "asteroid"],
    )

    assert hand(game, 0) == ["asteroid"]
    assert game.full_view()["discard"] == ["mine"]
    assert resources(game, 0)["titanium"] == 6
    assert game.decision["kind"] == "action"
