"""#206 Special Design (4 MegaCredits, science and Event Tags): the next card you play this
Generation is +2 or -2 steps in global requirements, your choice."""

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


def test_special_design_has_no_requirements_and_costs_4_megacredits():
    game = scenario(player(megacredits=4, hand=["special_design"]), player())

    pick(game, "Play Special Design (4 MegaCredits)")

    assert resources(game, 0)["megacredits"] == 0
    assert player_board(game, 0)["next_card"] == "special_design"


def test_after_special_design_the_next_card_played_is_2_steps_easier_to_meet():
    # Breathing Filters needs 7 % Oxygen and Windmills 7 % too.
    holding = player(megacredits=30, hand=["special_design", "breathing_filters", "windmills"])
    game = scenario(holding, player(), oxygen=5)
    assert not offered(game, "Play Breathing Filters")

    pick(game, "Play Special Design")
    assert offered(game, "Play Breathing Filters")
    assert offered(game, "Play Windmills")
    pick(game, "Play Breathing Filters")
    pick(game, "Pass")  # Player 2

    assert player_board(game, 0)["next_card"] is None
    assert game.decision["player"] == 0
    assert not offered(game, "Play Windmills")


def test_special_design_is_used_up_by_the_next_card_even_one_without_a_global_requirement():
    holding = player(megacredits=30, hand=["special_design", "mine", "breathing_filters"])
    game = scenario(holding, player(), oxygen=5)

    pick(game, "Play Special Design")
    pick(game, "Play Mine")
    pick(game, "Pass")  # Player 2

    assert game.decision["player"] == 0
    assert not offered(game, "Play Breathing Filters")


def test_special_design_lasts_only_until_the_end_of_the_generation():
    game = scenario(
        player(megacredits=30, hand=["special_design", "breathing_filters"]), player(), oxygen=5, draft=False
    )

    pick(game, "Play Special Design")
    end_the_generation(game)

    assert player_board(game, 0)["next_card"] is None
    if game.decision["player"] != 0:
        pick(game, "Pass")
    assert not offered(game, "Play Breathing Filters")


def test_special_design_and_adaptation_technology_add_up_to_4_steps():
    holding = player(
        megacredits=30, hand=["special_design", "breathing_filters"], played_cards=["adaptation_technology"]
    )
    game = scenario(holding, player(), oxygen=3)

    pick(game, "Play Special Design")

    assert offered(game, "Play Breathing Filters")


def test_special_design_is_worth_no_victory_points():
    game = scenario(player(played_cards=["special_design"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
