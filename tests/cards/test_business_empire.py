"""#P06 Business Empire (Prelude Card): increase your MegaCredit Production 6 steps. Pay 6 MegaCredits."""

from tests.helpers import (
    labels,
    pick,
    player,
    player_board,
    production,
    resources,
    scenario,
)


def test_business_empire_raises_megacredit_production_6_steps_and_costs_6_megacredits():
    game = scenario(player(prelude_cards=["business_empire"], megacredits=10), player(), prelude=True)

    assert production(game, 0)["megacredits"] == 6
    assert resources(game, 0)["megacredits"] == 4
    assert player_board(game, 0)["played_prelude_cards"] == ["business_empire"]
    assert "Player 1 pays 6 MegaCredits for Business Empire." in game.log
    assert game.decision["kind"] == "action"


def test_helions_heat_may_pay_for_it():
    game = scenario(
        player(prelude_cards=["business_empire"], corporation="helion", megacredits=4, heat=5),
        player(),
        prelude=True,
    )

    assert game.decision["kind"] == "payment"
    assert labels(game) == ["Pay 4 MegaCredits and 2 heat", "Pay 3 MegaCredits and 3 heat",
                            "Pay 2 MegaCredits and 4 heat", "Pay 1 MegaCredit and 5 heat"]
    pick(game, type="payment", heat=4)

    assert resources(game, 0)["megacredits"] == 2
    assert resources(game, 0)["heat"] == 1
    assert production(game, 0)["megacredits"] == 6


def test_with_fewer_than_6_megacredits_it_cant_be_played_and_is_discarded_for_15_megacredits():
    game = scenario(player(prelude_cards=["business_empire"], megacredits=5), player(), prelude=True)

    assert resources(game, 0)["megacredits"] == 20
    assert production(game, 0)["megacredits"] == 0
    assert player_board(game, 0)["played_prelude_cards"] == []
    assert "Player 1 can't play Business Empire, so they discard it and gain 15 MegaCredits." in game.log


def test_another_players_heat_doesnt_count():
    game = scenario(player(prelude_cards=["business_empire"], megacredits=5, heat=10), player(), prelude=True)

    assert player_board(game, 0)["played_prelude_cards"] == []
    assert resources(game, 0)["heat"] == 10
