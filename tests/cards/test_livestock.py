"""#184 Livestock (13 MegaCredits, animal Tag, requires 9 % Oxygen): Action: add 1 animal to this card.
Decrease your plant Production 1 step and increase your MegaCredit Production 2 steps. 1 Victory Point
for each animal on this card."""

from tests.helpers import (
    card_resources,
    final_scores,
    offered,
    pick,
    player,
    production,
    scenario,
    terraformed_mars,
)


def hand(plants=1):
    return player(megacredits=13, hand=["livestock"], production={"plants": plants})


def test_livestock_requires_9_percent_oxygen():
    assert not offered(scenario(hand(), player(), oxygen=8), "Play Livestock")
    assert offered(scenario(hand(), player(), oxygen=9), "Play Livestock")


def test_it_trades_the_players_own_plant_production_for_megacredit_production():
    game = scenario(hand(plants=2), player(production={"plants": 5}), oxygen=9)

    pick(game, "Play Livestock (13 MegaCredits)")

    assert production(game, 0)["plants"] == 1
    assert production(game, 0)["megacredits"] == 2
    assert production(game, 1)["plants"] == 5
    assert card_resources(game, 0) == {"livestock": 0}


def test_it_needs_plant_production_of_the_players_own_to_lower():
    other = player(production={"plants": 5})

    assert not offered(scenario(hand(plants=0), other, oxygen=9), "Play Livestock")


def test_the_action_adds_1_animal():
    game = scenario(player(played_cards=["livestock"]), player())

    pick(game, "Use the action of Livestock")

    assert card_resources(game, 0) == {"livestock": 1}


def test_livestock_scores_1_victory_point_for_each_animal():
    for animals in (0, 1, 6):
        holding = player(
            played_cards=["livestock"], card_resources={"livestock": animals}
        )

        game = scenario(holding, player(), **terraformed_mars())
        assert final_scores(game)[0]["cards"] == animals
