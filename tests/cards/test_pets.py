"""#172 Pets (10 MegaCredits, animal and Earth Tags): Effect: when any City Tile is placed, add an animal
to this card. Animals may not be removed from this card. Add 1 animal to this card. 1 Victory Point
per 2 animals here."""

from tests.helpers import (
    card_resources,
    final_scores,
    labels,
    ocean,
    offered,
    pick,
    player,
    scenario,
    terraformed_mars,
)


def test_it_has_no_requirement_and_comes_with_1_animal():
    game = scenario(player(megacredits=10, hand=["pets"]), player())

    pick(game, "Play Pets (10 MegaCredits)")

    assert card_resources(game, 0) == {"pets": 1}


def test_a_city_the_player_places_adds_an_animal():
    playing = player(megacredits=25, played_cards=["pets"])
    game = scenario(playing, player())

    pick(game, "City (25 MegaCredits)")
    pick(game, area="C4")

    assert card_resources(game, 0) == {"pets": 1}
    assert "Player 1's Pets takes effect." in game.log


def test_a_city_another_player_places_adds_an_animal_too():
    game = scenario(
        player(megacredits=25), player(played_cards=["pets"]), first_player=0
    )

    pick(game, "City (25 MegaCredits)")
    pick(game, area="C4")

    assert card_resources(game, 1) == {"pets": 1}
    assert "Player 2 adds 1 animal to Pets." in game.log


def test_capitals_city_counts_as_a_city():
    playing = player(
        megacredits=26,
        hand=["capital"],
        played_cards=["pets"],
        production={"energy": 2},
    )
    oceans = [ocean(area) for area in ("A2", "A4", "A5", "B6")]
    game = scenario(playing, player(), tiles=oceans)

    pick(game, "Play Capital")
    pick(game, area="C4")

    assert card_resources(game, 0) == {"pets": 1}


def test_other_tiles_add_nothing():
    playing = player(plants=8, played_cards=["pets"])
    game = scenario(playing, player())

    pick(game, "Convert 8 plants")
    pick(game, area="C4")

    assert card_resources(game, 0) == {"pets": 0}


def test_predators_cannot_remove_animals_from_pets_even_the_players_own():
    game = scenario(
        player(played_cards=["predators", "pets"], card_resources={"pets": 3}),
        player(played_cards=["fish"]),
    )

    assert not offered(game, "Use the action of Predators")


def test_predators_leaves_pets_out_of_the_cards_it_may_take_from():
    game = scenario(
        player(played_cards=["predators"]),
        player(
            played_cards=["fish", "pets", "birds"],
            card_resources={"fish": 1, "pets": 3, "birds": 1},
        ),
    )

    pick(game, "Use the action of Predators")

    assert labels(game) == [
        "Remove 1 animal from Player 2's Fish",
        "Remove 1 animal from Player 2's Birds",
    ]


def test_virus_cannot_remove_animals_from_pets():
    game = scenario(
        player(megacredits=1, hand=["virus"]),
        player(played_cards=["pets"], card_resources={"pets": 3}),
    )

    pick(game, "Play Virus")

    assert card_resources(game, 1) == {"pets": 3}
    assert game.decision["kind"] == "action"


def test_ceos_favorite_project_may_add_to_pets():
    playing = player(
        megacredits=1,
        hand=["ceos_favorite_project"],
        played_cards=["pets"],
        card_resources={"pets": 1},
    )
    game = scenario(playing, player())

    pick(game, "Play CEO's Favorite Project")

    assert card_resources(game, 0) == {"pets": 2}


def test_pets_scores_1_victory_point_per_2_animals():
    for animals, points in ((1, 0), (2, 1), (5, 2)):
        holding = player(played_cards=["pets"], card_resources={"pets": animals})

        game = scenario(holding, player(), **terraformed_mars())
        assert final_scores(game)[0]["cards"] == points


def test_a_city_off_mars_adds_an_animal_too():
    playing = player(megacredits=20, hand=["ganymede_colony"], played_cards=["pets"])
    game = scenario(playing, player())

    pick(game, "Play Ganymede Colony")
    pick(game, area="ganymede_colony")

    assert card_resources(game, 0) == {"pets": 1}
