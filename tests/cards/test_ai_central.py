"""#208 AI Central (Corporate Era, 21 MegaCredits, building and science Tags, 1 Victory Point):
requires 3 science Tags. Action: draw 2 cards. Decrease your energy Production 1 step."""

from tests.helpers import (
    final_scores,
    hand,
    offered,
    pick,
    player,
    production,
    resources,
    scenario,
    terraformed_mars,
)

# Each of these has one science Tag.
THREE_SCIENCE_TAGS = ["development_center", "inventors_guild", "restricted_area"]


def test_ai_central_needs_3_science_tags():
    two = player(production={"energy": 1}, hand=["ai_central"], played_cards=THREE_SCIENCE_TAGS[:2])
    assert not offered(scenario(two, player()), "Play AI Central")
    three = player(production={"energy": 1}, hand=["ai_central"], played_cards=THREE_SCIENCE_TAGS)
    assert offered(scenario(three, player()), "Play AI Central")


def test_ai_central_needs_energy_production_to_lower():
    holding = player(hand=["ai_central"], played_cards=THREE_SCIENCE_TAGS)

    assert not offered(scenario(holding, player()), "Play AI Central")


def test_ai_central_lowers_energy_production_1_step():
    holding = player(megacredits=21, production={"energy": 1}, hand=["ai_central"], played_cards=THREE_SCIENCE_TAGS)
    game = scenario(holding, player())

    pick(game, "Play AI Central (21 MegaCredits)")

    assert production(game, 0)["energy"] == 0
    assert resources(game, 0)["megacredits"] == 0


def test_ai_centrals_action_draws_2_cards_for_nothing():
    game = scenario(player(megacredits=5, played_cards=["ai_central"]), player(), deck=["mine", "trees", "birds"])

    pick(game, "Use the action of AI Central")

    assert hand(game, 0) == ["mine", "trees"]
    assert resources(game, 0) == {"megacredits": 5, "steel": 0, "titanium": 0, "plants": 0, "energy": 0, "heat": 0}
    assert "Player 1 draws 2 cards." in game.log


def test_robotic_workforce_copies_ai_centrals_production_box():
    holding = player(megacredits=9, production={"energy": 2}, hand=["robotic_workforce"], played_cards=["ai_central"])
    game = scenario(holding, player())

    pick(game, "Play Robotic Workforce")

    assert production(game, 0)["energy"] == 1


def test_ai_central_is_worth_1_victory_point():
    game = scenario(player(played_cards=["ai_central"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [1, 0]
