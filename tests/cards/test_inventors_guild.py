"""#006 Inventors' Guild (Corporate Era, 9 MegaCredits, science Tag): Action: look at the top card
and either buy it or discard it."""

from tests.helpers import (
    final_scores,
    hand,
    keeping,
    labels,
    offered,
    pick,
    player,
    resources,
    scenario,
    terraformed_mars,
)


def test_inventors_guild_has_no_requirements_and_does_nothing_when_played():
    game = scenario(player(megacredits=9, hand=["inventors_guild"]), player())

    pick(game, "Play Inventors' Guild (9 MegaCredits)")

    assert resources(game, 0)["megacredits"] == 0
    assert hand(game, 0) == []


def test_inventors_guilds_action_looks_at_the_top_card_to_buy_it_or_discard_it():
    game = scenario(player(megacredits=5, played_cards=["inventors_guild"]), player(), deck=["mine", "trees"])

    pick(game, "Use the action of Inventors' Guild")

    assert game.decision["kind"] == "keep_cards"
    assert labels(game) == ["Buy Mine (3 MegaCredits)", "Done"]
    assert keeping(game, 0) == {
        "card": "inventors_guild",
        "looking_at": ["mine"],
        "kept": [],
        "keep": 1,
        "price": 3,
    }
    assert keeping(game, 1) is None
    assert "Player 1 looks at the top card of the deck." in game.log


def test_buying_the_card_pays_3_megacredits_and_takes_it_into_the_hand():
    game = scenario(player(megacredits=5, played_cards=["inventors_guild"]), player(), deck=["mine", "trees"])

    pick(game, "Use the action of Inventors' Guild")
    pick(game, type="buy_card", card="mine")

    assert hand(game, 0) == ["mine"]
    assert resources(game, 0)["megacredits"] == 2
    assert keeping(game, 0) is None
    assert "Player 1 buys 1 card for 3 MegaCredits and discards 0." in game.log
    assert game.decision["kind"] == "action"
    assert offered(game, "End Turn")


def test_done_discards_the_card_without_paying():
    game = scenario(player(megacredits=5, played_cards=["inventors_guild"]), player(), deck=["mine", "trees"])

    pick(game, "Use the action of Inventors' Guild")
    pick(game, "Done")

    assert hand(game, 0) == []
    assert resources(game, 0)["megacredits"] == 5
    assert game.full_view()["discard"] == ["mine"]
    assert "Player 1 buys none of them and discards 1." in game.log
    assert game.decision["kind"] == "action"


def test_with_fewer_than_3_megacredits_the_card_is_looked_at_and_discarded_without_a_decision():
    game = scenario(player(megacredits=2, played_cards=["inventors_guild"]), player(), deck=["mine", "trees"])

    pick(game, "Use the action of Inventors' Guild")

    assert game.full_view()["discard"] == ["mine"]
    assert resources(game, 0)["megacredits"] == 2
    assert game.decision["kind"] == "action"


def test_inventors_guild_has_no_victory_points():
    game = scenario(player(played_cards=["inventors_guild"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
