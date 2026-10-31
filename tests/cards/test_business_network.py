"""#110 Business Network (Corporate Era, 4 MegaCredits, Earth Tag): Action: look at the top card
and either buy it or discard it. Decrease your MegaCredit Production 1 step."""

from tests.helpers import (
    final_scores,
    hand,
    labels,
    offered,
    pick,
    player,
    production,
    resources,
    scenario,
    terraformed_mars,
)


def test_business_network_lowers_megacredit_production_1_step():
    game = scenario(player(megacredits=4, hand=["business_network"]), player())

    pick(game, "Play Business Network (4 MegaCredits)")

    assert production(game, 0)["megacredits"] == -1
    assert resources(game, 0)["megacredits"] == 0


def test_business_network_cannot_take_megacredit_production_below_minus_5():
    holding = player(production={"megacredits": -5}, hand=["business_network"])

    assert not offered(scenario(holding, player()), "Play Business Network")


def test_business_networks_action_looks_at_the_top_card_to_buy_it_or_discard_it():
    game = scenario(player(megacredits=3, played_cards=["business_network"]), player(), deck=["trees", "mine"])

    pick(game, "Use the action of Business Network")
    assert labels(game) == ["Buy Trees (3 MegaCredits)", "Done"]
    pick(game, "Buy Trees")

    assert hand(game, 0) == ["trees"]
    assert resources(game, 0)["megacredits"] == 0


def test_done_discards_the_card_business_network_looked_at():
    game = scenario(player(megacredits=3, played_cards=["business_network"]), player(), deck=["trees", "mine"])

    pick(game, "Use the action of Business Network")
    pick(game, "Done")

    assert hand(game, 0) == []
    assert resources(game, 0)["megacredits"] == 3
    assert game.full_view()["discard"] == ["trees"]


def test_business_network_has_no_victory_points():
    game = scenario(player(played_cards=["business_network"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
