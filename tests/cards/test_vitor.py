"""Vitor (Prelude's Corporation, Earth Tag): Effect: when you play a card with a NON-NEGATIVE VP icon, including this,
gain 3 MegaCredits. You start with 45 MegaCredits. As your first action, fund an award for free.

Vitor has no VP icon itself, but "including this" makes it count, as in the open-source game: it starts with 45 and
gains 3 once revealed (see docs/rules-notes.md)."""

from tests.helpers import (
    award,
    funded,
    labels,
    offered,
    pick,
    player,
    player_board,
    resources,
    scenario,
    start_as,
)


def test_vitor_starts_with_45_megacredits_and_gains_3_for_itself():
    game, first = start_as("vitor", prelude=True)

    assert resources(game, first)["megacredits"] == 48
    assert player_board(game, first)["tags"]["earth"] == 1
    assert f"Player {first + 1}'s Vitor takes effect." in game.log
    assert player_board(game, first)["first_action_due"] is True


def test_a_card_with_victory_points_gains_3_megacredits_and_one_without_does_not():
    game = scenario(player(corporation="vitor", megacredits=20, hand=["mine", "tardigrades"]), player(), prelude=True)

    pick(game, "Play Mine")  # No VP icon.
    assert resources(game, 0)["megacredits"] == 16
    pick(game, "Play Tardigrades")  # 1 Victory Point per 4 microbes: its icon is 1.
    assert resources(game, 0)["megacredits"] == 16 - 4 + 3
    assert "Player 1's Vitor takes effect." in game.log


def test_a_card_with_negative_victory_points_gains_nothing():
    game = scenario(player(corporation="vitor", megacredits=10, hand=["hackers"], production={"energy": 1}), player(),
                    prelude=True)

    pick(game, "Play Hackers")  # -1 Victory Point; it lowers Player 2's MegaCredit Production, the only choice.

    assert resources(game, 0)["megacredits"] == 7


def test_an_event_with_victory_points_counts_too():
    game = scenario(player(corporation="vitor", megacredits=9, hand=["martian_survey"]), player(), prelude=True)

    pick(game, "Play Martian Survey")

    assert resources(game, 0)["megacredits"] == 3


def test_its_first_action_funds_an_award_of_its_players_choice_for_free():
    game = scenario(player(corporation="vitor", first_action_due=True, megacredits=0), player(),
                    prelude=True, awards=[funded("landlord", by=1)])

    assert labels(game) == ["First action of Vitor: fund an Award for free", "Pass"]
    pick(game, "First action")

    assert labels(game) == [
        "Fund the Banker Award (0 MegaCredits)",
        "Fund the Scientist Award (0 MegaCredits)",
        "Fund the Thermalist Award (0 MegaCredits)",
        "Fund the Miner Award (0 MegaCredits)",
    ]
    pick(game, "Fund the Miner Award")
    assert award(game, "miner")["funded_by"] == 0
    assert resources(game, 0)["megacredits"] == 0
    assert "Player 1 funds the Miner Award for 0 MegaCredits." in game.log
    assert game.full_view()["award_cost"] == 20
    assert game.full_view()["actions_this_turn"] == 1


def test_with_3_awards_funded_it_goes_without_its_first_action():
    awards = [funded("landlord", by=1), funded("banker", by=1), funded("miner", by=1)]
    game = scenario(player(corporation="vitor", first_action_due=True), player(), prelude=True, awards=awards)

    assert not offered(game, "First action")
