"""United Nations Mars Initiative (Earth Tag): Action: if your Terraform Rating was raised this
Generation, you may pay 3 MegaCredits to raise it 1 step more. You start with 40 MegaCredits."""

from tests.helpers import (
    end_the_generation,
    offered,
    pick,
    player,
    player_board,
    production,
    resources,
    scenario,
    start_as,
)

ACTION = "Use the action of United Nations Mars Initiative"


def test_it_starts_with_40_megacredits_and_an_earth_tag():
    game, first = start_as("united_nations_mars_initiative")

    assert resources(game, first) == {
        "megacredits": 40,
        "steel": 0,
        "titanium": 0,
        "plants": 0,
        "energy": 0,
        "heat": 0,
    }
    assert set(production(game, first).values()) == {0}
    assert player_board(game, first)["tags"]["earth"] == 1


def test_its_action_is_not_offered_until_the_terraform_rating_was_raised_this_generation():
    game = scenario(player(corporation="united_nations_mars_initiative"), player())

    assert not offered(game, ACTION)
    assert player_board(game, 0)["terraform_rating_raised"] is False

    pick(game, "Asteroid")

    assert player_board(game, 0)["terraform_rating_raised"] is True
    assert offered(game, ACTION)


def test_it_pays_3_megacredits_to_raise_the_terraform_rating_1_step_once_per_generation():
    game = scenario(
        player(corporation="united_nations_mars_initiative", megacredits=17), player()
    )
    pick(game, "Asteroid")

    pick(game, ACTION)

    assert resources(game, 0)["megacredits"] == 0
    assert player_board(game, 0)["terraform_rating"] == 22
    assert player_board(game, 0)["used_actions"] == ["united_nations_mars_initiative"]
    assert (
        game.decision["player"] == 1
    )  # Two Actions end the Turn; the action is used for this Generation.


def test_without_3_megacredits_it_is_not_offered():
    game = scenario(
        player(corporation="united_nations_mars_initiative", megacredits=16), player()
    )
    pick(game, "Asteroid")

    assert not offered(game, ACTION)


def test_the_raise_is_forgotten_when_the_generation_ends():
    game = scenario(player(corporation="united_nations_mars_initiative"), player())
    pick(game, "Asteroid")

    end_the_generation(game)

    assert player_board(game, 0)["terraform_rating_raised"] is False
    assert player_board(game, 0)["used_actions"] == []
    pick(game, "Pass")  # Player 2 holds the first-player marker now.
    assert game.decision["player"] == 0
    assert not offered(game, ACTION)


def test_any_raise_counts_an_ocean_oxygen_and_a_card_alike():
    ocean = scenario(player(corporation="united_nations_mars_initiative"), player())
    pick(ocean, "Aquifer")
    pick(ocean, type="area", area="A2")
    assert offered(ocean, ACTION)

    greenery = scenario(player(corporation="united_nations_mars_initiative"), player())
    pick(greenery, "Greenery (")
    pick(greenery, type="area", area="C3")
    assert offered(greenery, ACTION)

    card = scenario(
        player(corporation="united_nations_mars_initiative", hand=["bribed_committee"]),
        player(),
    )
    pick(card, "Play Bribed Committee")
    assert offered(card, ACTION)


def test_another_players_raise_does_not_count():
    game = scenario(player(), player(corporation="united_nations_mars_initiative"))

    pick(game, "Asteroid")
    pick(game, "End Turn")

    assert not offered(game, ACTION)
