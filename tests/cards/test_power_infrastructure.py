"""#194 Power Infrastructure (Corporate Era, 4 MegaCredits, building and power Tags): Action: spend
any amount of energy and gain that amount of MegaCredits."""

from tests.helpers import final_scores, labels, offered, pick, player, resources, scenario, terraformed_mars


def test_power_infrastructure_has_no_requirements_and_does_nothing_when_played():
    game = scenario(player(megacredits=4, hand=["power_infrastructure"]), player())

    pick(game, "Play Power Infrastructure (4 MegaCredits)")

    assert resources(game, 0)["megacredits"] == 0


def test_power_infrastructures_action_asks_how_much_energy_to_spend_from_1_to_all_of_it():
    game = scenario(player(megacredits=0, energy=3, played_cards=["power_infrastructure"]), player())

    pick(game, "Use the action of Power Infrastructure")

    assert game.decision["kind"] == "resources"
    assert labels(game) == [
        "Spend 1 energy to gain 1 MegaCredit",
        "Spend 2 energy to gain 2 MegaCredits",
        "Spend 3 energy to gain 3 MegaCredits",
    ]
    assert game.decision["options"][1]["details"] == {
        "type": "choose_resources",
        "card": "power_infrastructure",
        "resources": {"megacredits": 2, "steel": 0, "titanium": 0, "plants": 0, "energy": -2, "heat": 0},
    }
    pick(game, "Spend 2 energy")
    assert resources(game, 0)["energy"] == 1
    assert resources(game, 0)["megacredits"] == 2
    assert game.decision["kind"] == "action"


def test_with_1_energy_power_infrastructure_spends_it_without_a_decision():
    game = scenario(player(megacredits=0, energy=1, played_cards=["power_infrastructure"]), player())

    pick(game, "Use the action of Power Infrastructure")

    assert resources(game, 0)["energy"] == 0
    assert resources(game, 0)["megacredits"] == 1
    assert game.decision["kind"] == "action"


def test_power_infrastructures_action_needs_energy():
    assert not offered(scenario(player(played_cards=["power_infrastructure"]), player()), type="use_action")


def test_power_infrastructure_has_no_victory_points():
    game = scenario(player(played_cards=["power_infrastructure"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
