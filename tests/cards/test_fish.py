"""#052 Fish (9 MegaCredits, animal Tag, requires +2 °C or warmer): Action: add 1 animal to this card.
Decrease any plant Production 1 step. 1 Victory Point for each animal on this card."""

from tests.helpers import (
    card_resources,
    final_scores,
    labels,
    offered,
    pick,
    player,
    production,
    scenario,
    terraformed_mars,
)


def playing_fish():
    return player(megacredits=9, hand=["fish"])


def test_fish_requires_plus_2_degrees():
    other = player(production={"plants": 1})

    assert not offered(scenario(playing_fish(), other, temperature=0), "Play Fish")
    assert offered(scenario(playing_fish(), other, temperature=2), "Play Fish")


def test_it_lowers_the_only_opponents_plant_production_without_a_decision():
    game = scenario(playing_fish(), player(production={"plants": 2}), temperature=2)

    pick(game, "Play Fish (9 MegaCredits)")

    assert production(game, 1)["plants"] == 1
    assert card_resources(game, 0) == {"fish": 0}
    assert "Player 1 lowers Player 2's plant Production by 1." in game.log
    assert game.decision["kind"] == "action"


def test_the_player_picks_whose_plant_production_it_lowers():
    game = scenario(
        playing_fish(),
        player(production={"plants": 1}),
        player(production={"plants": 3}),
        temperature=2,
    )

    pick(game, "Play Fish")

    assert labels(game) == [
        "Lower Player 2's plant Production by 1",
        "Lower Player 3's plant Production by 1",
    ]
    pick(game, "Player 3")
    assert production(game, 2)["plants"] == 2


def test_with_only_their_own_plant_production_to_lower_the_player_lowers_it():
    playing = player(megacredits=9, hand=["fish"], production={"plants": 1})
    game = scenario(playing, player(), temperature=2)

    pick(game, "Play Fish")

    assert production(game, 0)["plants"] == 0


def test_it_is_not_offered_with_nobody_to_lose_plant_production():
    assert not offered(scenario(playing_fish(), player(), temperature=2), "Play Fish")


def test_the_action_adds_1_animal_once_per_generation():
    game = scenario(player(played_cards=["fish"]), player())

    pick(game, "Use the action of Fish")

    assert card_resources(game, 0) == {"fish": 1}
    assert "Player 1 adds 1 animal to Fish." in game.log
    assert not offered(game, "Use the action of Fish")


def test_fish_scores_1_victory_point_for_each_animal():
    for animals in (0, 1, 5):
        holding = player(played_cards=["fish"], card_resources={"fish": animals})

        game = scenario(holding, player(), **terraformed_mars())
        assert final_scores(game)[0]["cards"] == animals
