"""#195 Indentured Workers (Corporate Era, 0 MegaCredits, Event Tag, -1 Victory Point): the next
card you play this Generation costs 8 MegaCredits less."""

from tests.helpers import (
    end_the_generation,
    final_scores,
    offered,
    pick,
    player,
    player_board,
    resources,
    scenario,
    terraformed_mars,
)


def test_indentured_workers_has_no_requirements_and_costs_nothing():
    game = scenario(player(megacredits=0, hand=["indentured_workers"]), player())

    pick(game, "Play Indentured Workers (0 MegaCredits)")

    assert player_board(game, 0)["next_card"] == "indentured_workers"
    assert "Player 1 plays Indentured Workers, paying 0 MegaCredits." in game.log


def test_after_indentured_workers_the_next_card_played_costs_8_megacredits_less():
    game = scenario(player(megacredits=10, hand=["indentured_workers", "satellites", "sponsors"]), player())

    pick(game, "Play Indentured Workers")
    assert offered(game, "Play Satellites (2 MegaCredits)", cost=2)
    assert offered(game, "Play Sponsors (0 MegaCredits)", cost=0)
    pick(game, "Play Satellites")
    pick(game, "Pass")  # Player 2

    assert resources(game, 0)["megacredits"] == 8
    assert player_board(game, 0)["next_card"] is None
    assert not offered(game, "Play Sponsors (0 MegaCredits)")
    assert offered(game, "Play Sponsors (6 MegaCredits)")


def test_indentured_workers_lasts_only_until_the_end_of_the_generation():
    game = scenario(player(megacredits=10, hand=["indentured_workers", "satellites"]), player(), draft=False)

    pick(game, "Play Indentured Workers")
    end_the_generation(game)

    assert player_board(game, 0)["next_card"] is None
    if game.decision["player"] != 0:
        pick(game, "Pass")
    assert offered(game, "Play Satellites (10 MegaCredits)")


def test_indentured_workers_does_not_make_a_standard_project_cheaper():
    game = scenario(player(megacredits=10, hand=["indentured_workers", "mine"]), player())

    pick(game, "Play Indentured Workers")

    assert not offered(game, "Power Plant")


def test_special_design_played_after_indentured_workers_uses_it_up_and_costs_nothing():
    game = scenario(player(megacredits=0, hand=["indentured_workers", "special_design"]), player())

    pick(game, "Play Indentured Workers")
    pick(game, "Play Special Design (0 MegaCredits)")

    assert player_board(game, 0)["next_card"] == "special_design"


def test_indentured_workers_is_worth_minus_1_victory_point():
    game = scenario(player(played_cards=["indentured_workers"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [-1, 0]
