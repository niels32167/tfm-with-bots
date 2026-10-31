"""#069 Electro Catapult (Corporate Era, 17 MegaCredits, building Tag, 1 Victory Point): Oxygen
must be 8 % or less. Action: spend 1 plant or 1 steel to gain 7 MegaCredits. Decrease your energy
Production 1 step."""

from tests.helpers import (
    final_scores,
    labels,
    offered,
    pick,
    player,
    production,
    resources,
    scenario,
    terraformed_mars,
)


def test_electro_catapult_needs_8_percent_oxygen_or_less():
    holding = player(production={"energy": 1}, hand=["electro_catapult"])
    assert offered(scenario(holding, player(), oxygen=8), "Play Electro Catapult")
    assert not offered(scenario(holding, player(), oxygen=9), "Play Electro Catapult")


def test_electro_catapult_needs_energy_production_to_lower():
    assert not offered(scenario(player(hand=["electro_catapult"]), player()), "Play Electro Catapult")


def test_electro_catapult_lowers_energy_production_1_step():
    game = scenario(player(megacredits=17, production={"energy": 1}, hand=["electro_catapult"]), player())

    pick(game, "Play Electro Catapult (17 MegaCredits)")

    assert production(game, 0)["energy"] == 0
    assert resources(game, 0)["megacredits"] == 0


def test_with_a_plant_and_a_steel_electro_catapults_action_asks_which_to_spend():
    game = scenario(player(megacredits=0, plants=1, steel=1, played_cards=["electro_catapult"]), player())

    pick(game, "Use the action of Electro Catapult")

    assert game.decision["kind"] == "resources"
    assert labels(game) == ["Spend 1 plant to gain 7 MegaCredits", "Spend 1 steel to gain 7 MegaCredits"]
    pick(game, "Spend 1 steel to gain 7 MegaCredits")

    assert resources(game, 0) == {"megacredits": 7, "steel": 0, "titanium": 0, "plants": 1, "energy": 0, "heat": 0}
    assert game.decision["kind"] == "action"


def test_with_only_steel_electro_catapult_spends_it_without_a_decision():
    game = scenario(player(megacredits=0, steel=2, played_cards=["electro_catapult"]), player())

    pick(game, "Use the action of Electro Catapult")

    assert resources(game, 0)["steel"] == 1
    assert resources(game, 0)["megacredits"] == 7
    assert game.decision["kind"] == "action"


def test_electro_catapults_action_needs_a_plant_or_a_steel():
    game = scenario(player(heat=5, energy=5, played_cards=["electro_catapult"]), player())

    assert not offered(game, type="use_action")


def test_electro_catapults_action_is_offered_whatever_the_oxygen_once_it_is_played():
    game = scenario(player(plants=1, played_cards=["electro_catapult"]), player(), oxygen=14)

    assert offered(game, "Use the action of Electro Catapult")


def test_robotic_workforce_copies_electro_catapults_production_box():
    holding = player(
        megacredits=9, production={"energy": 1}, hand=["robotic_workforce"], played_cards=["electro_catapult"]
    )
    game = scenario(holding, player())

    pick(game, "Play Robotic Workforce")

    assert production(game, 0)["energy"] == 0


def test_electro_catapult_is_worth_1_victory_point():
    game = scenario(player(played_cards=["electro_catapult"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [1, 0]
