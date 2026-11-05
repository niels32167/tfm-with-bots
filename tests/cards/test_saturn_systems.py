"""Saturn Systems (Corporate Era, jovian Tag): Effect: each time any jovian Tag is put into play,
including this, increase your MegaCredit Production 1 step. You start with 1 titanium Production and 42
MegaCredits."""

from tests.helpers import (
    pick,
    player,
    player_board,
    production,
    resources,
    scenario,
    start_as,
)


def test_saturn_systems_starts_with_1_titanium_production_42_megacredits_and_its_own_tag_counted():
    game, first = start_as("saturn_systems")

    assert resources(game, first) == {
        "megacredits": 42,
        "steel": 0,
        "titanium": 0,
        "plants": 0,
        "energy": 0,
        "heat": 0,
    }
    assert production(game, first) == {
        "megacredits": 1,
        "steel": 0,
        "titanium": 1,
        "plants": 0,
        "energy": 0,
        "heat": 0,
    }
    assert player_board(game, first)["tags"]["jovian"] == 1


def test_its_own_players_jovian_card_raises_megacredit_production():
    game = scenario(
        player(corporation="saturn_systems", hand=["vesta_shipyard"]), player()
    )

    pick(game, "Play Vesta Shipyard")

    assert production(game, 0)["megacredits"] == 1


def test_another_players_jovian_card_raises_it_too():
    game = scenario(
        player(hand=["vesta_shipyard"]), player(corporation="saturn_systems")
    )

    pick(game, "Play Vesta Shipyard")

    assert production(game, 1)["megacredits"] == 1
    assert production(game, 0)["megacredits"] == 0


def test_a_card_without_a_jovian_tag_changes_nothing():
    game = scenario(player(hand=["sponsors"]), player(corporation="saturn_systems"))

    pick(game, "Play Sponsors")

    assert production(game, 1)["megacredits"] == 0
