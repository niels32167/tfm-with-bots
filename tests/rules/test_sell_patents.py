"""Sell Patents, the Standard Project printed first on the board: a Player picks cards from their
hand one at a time, then Done, and gains 1 MegaCredit for each. The cards go face down to the
discard pile."""

from tests.helpers import hand, labels, offered, pick, player, resources, scenario


def test_sell_patents_is_offered_only_to_a_player_with_a_card_in_hand():
    assert offered(scenario(player(hand=["birds"]), player()), project="sell_patents", cost=0)
    assert not offered(scenario(player(), player()), project="sell_patents")


def test_selling_patents_is_a_chain_of_single_picks_ending_with_done():
    game = scenario(player(megacredits=0, hand=["birds", "mine", "trees"]), player())

    pick(game, "Sell Patents (1 MegaCredit per card)")

    assert game.decision["kind"] == "sell_patents"
    # In card-number order; Done only once a card is sold, since selling none would waste the Action.
    assert labels(game) == ["Sell Mine (1 MegaCredit)", "Sell Trees (1 MegaCredit)", "Sell Birds (1 MegaCredit)"]
    assert game.decision["options"][0]["details"] == {"type": "sell_card", "card": "mine", "megacredits": 1}

    pick(game, type="sell_card", card="birds")
    assert labels(game) == ["Sell Mine (1 MegaCredit)", "Sell Trees (1 MegaCredit)", "Done"]
    pick(game, type="sell_card", card="mine")
    pick(game, "Done")

    assert hand(game, 0) == ["trees"]
    assert resources(game, 0)["megacredits"] == 2
    assert game.full_view()["discard"] == ["mine", "birds"]
    assert (game.player_view(1)["discard"], game.player_view(1)["discard_size"]) == (None, 2)
    assert game.log[-1] == "Player 1 sells 2 patents for 2 MegaCredits."
    assert (game.decision["kind"], game.player_view(0)["actions_this_turn"]) == ("action", 1)


def test_selling_the_last_card_in_hand_ends_the_action_without_done():
    game = scenario(player(megacredits=0, hand=["birds"]), player())

    pick(game, project="sell_patents")
    pick(game, type="sell_card", card="birds")

    assert hand(game, 0) == []
    assert game.log[-1] == "Player 1 sells 1 patent for 1 MegaCredit."
    assert (game.decision["kind"], game.player_view(0)["actions_this_turn"]) == ("action", 1)
