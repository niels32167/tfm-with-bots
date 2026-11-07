"""Robinson Industries (Prelude's Corporation, no Tag): Action: spend 4 MegaCredits to increase (one of) your LOWEST
PRODUCTION 1 step. You start with 47 MegaCredits."""

from tests.helpers import labels, offered, pick, player, production, resources, scenario, start_as


def robinson(**fields):
    return player(corporation="robinson_industries", **fields)


def test_robinson_industries_starts_with_47_megacredits_and_no_tag():
    game, first = start_as("robinson_industries", prelude=True)

    assert resources(game, first)["megacredits"] == 47
    assert set(production(game, first).values()) == {0}


def test_its_action_costs_4_megacredits_and_raises_one_of_the_lowest_productions_of_its_players_choice():
    game = scenario(
        robinson(
            megacredits=5,
            production={"megacredits": 2, "steel": 1, "titanium": 1, "plants": 3, "energy": 2, "heat": 1},
        ),
        player(),
        prelude=True,
    )

    pick(game, "Use the action of Robinson Industries")

    assert labels(game) == [
        "Raise steel Production by 1",
        "Raise titanium Production by 1",
        "Raise heat Production by 1",
    ]
    pick(game, "Raise titanium Production by 1")
    assert production(game, 0)["titanium"] == 2
    assert resources(game, 0)["megacredits"] == 1
    assert not offered(game, "Use the action of Robinson Industries")


def test_with_one_lowest_production_it_is_raised_without_a_decision():
    game = scenario(
        robinson(megacredits=4, production={"megacredits": 1, "steel": 1, "titanium": 1, "plants": 1, "energy": 1}),
        player(),
        prelude=True,
    )

    pick(game, "Use the action of Robinson Industries")

    assert production(game, 0)["heat"] == 1
    assert game.decision["kind"] == "action"


def test_megacredit_production_below_0_is_the_lowest():
    game = scenario(robinson(megacredits=4, production={"megacredits": -1}), player(), prelude=True)

    pick(game, "Use the action of Robinson Industries")

    assert production(game, 0)["megacredits"] == 0


def test_its_action_needs_4_megacredits():
    game = scenario(robinson(megacredits=3), player(), prelude=True)

    assert not offered(game, "Use the action of Robinson Industries")
