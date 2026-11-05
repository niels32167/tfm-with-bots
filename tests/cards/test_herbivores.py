"""#147 Herbivores (12 MegaCredits, animal Tag, requires 8 % Oxygen): Effect: when you place a Greenery
Tile, add an animal to this card. Add 1 animal to this card. Decrease any plant Production 1 step. 1
Victory Point per 2 animals on this card."""

from tests.helpers import (
    areas_offered,
    card_resources,
    end_the_action_phase,
    final_scores,
    offered,
    pick,
    player,
    production,
    scenario,
    terraformed_mars,
)


def test_herbivores_requires_8_percent_oxygen():
    hand = player(megacredits=12, hand=["herbivores"])
    other = player(production={"plants": 1})

    assert not offered(scenario(hand, other, oxygen=7), "Play Herbivores")
    assert offered(scenario(hand, other, oxygen=8), "Play Herbivores")


def test_it_comes_with_1_animal_and_lowers_any_plant_production_1_step():
    hand = player(megacredits=12, hand=["herbivores"])
    game = scenario(hand, player(production={"plants": 1}), oxygen=8)

    pick(game, "Play Herbivores (12 MegaCredits)")

    assert card_resources(game, 0) == {"herbivores": 1}
    assert production(game, 1)["plants"] == 0


def test_it_is_not_offered_with_nobody_to_lose_plant_production():
    hand = player(megacredits=12, hand=["herbivores"])

    assert not offered(scenario(hand, player(), oxygen=8), "Play Herbivores")


def test_a_greenery_the_player_places_adds_an_animal():
    playing = player(plants=8, played_cards=["herbivores"])
    game = scenario(playing, player())

    pick(game, "Convert 8 plants")
    pick(game, area=areas_offered(game)[0])

    assert card_resources(game, 0) == {"herbivores": 1}
    assert "Player 1's Herbivores takes effect." in game.log
    assert "Player 1 adds 1 animal to Herbivores." in game.log


def test_a_greenery_from_a_card_adds_an_animal_too():
    # Mangrove's Greenery goes on an Area reserved for Oceans.
    playing = player(megacredits=12, hand=["mangrove"], played_cards=["herbivores"])
    game = scenario(playing, player(), temperature=4)

    pick(game, "Play Mangrove")
    pick(game, area="A2")

    assert card_resources(game, 0) == {"herbivores": 1}


def test_another_players_greenery_adds_nothing():
    game = scenario(
        player(plants=8), player(played_cards=["herbivores"]), first_player=0
    )

    pick(game, "Convert 8 plants")
    pick(game, area=areas_offered(game)[0])

    assert card_resources(game, 1) == {"herbivores": 0}


def test_other_tiles_add_nothing():
    playing = player(megacredits=25, played_cards=["herbivores"])
    game = scenario(playing, player())

    pick(game, "City (25 MegaCredits)")
    pick(game, area="C4")

    assert card_resources(game, 0) == {"herbivores": 0}


def test_herbivores_scores_1_victory_point_per_2_animals():
    for animals, points in ((1, 0), (2, 1), (7, 3)):
        holding = player(
            played_cards=["herbivores"], card_resources={"herbivores": animals}
        )

        game = scenario(holding, player(), **terraformed_mars())
        assert final_scores(game)[0]["cards"] == points


def test_a_greenery_in_the_final_conversion_adds_an_animal_and_can_score():
    playing = player(
        plants=8,
        played_cards=["herbivores"],
        card_resources={"herbivores": 1},
    )
    game = scenario(playing, player(), **terraformed_mars())

    end_the_action_phase(game)
    pick(game, "Convert 8 plants")
    pick(game, area=areas_offered(game)[0])

    assert card_resources(game, 0) == {"herbivores": 2}
    assert game.is_over
    assert game.scores[0]["cards"] == 1
