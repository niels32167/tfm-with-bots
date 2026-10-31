"""#111 Business Contacts (7 MegaCredits, Event and Earth Tags): look at the top 4 cards from the
deck. Take 2 of them into hand and discard the other 2."""

from tests.helpers import (
    PROJECT_CARDS,
    final_scores,
    hand,
    keeping,
    labels,
    pick,
    player,
    player_board,
    scenario,
    terraformed_mars,
)

# Fish is #052, Mine #056, Trees #060 and Birds #072; the Options come in card-number order.
TOP_OF_THE_DECK = ["mine", "trees", "birds", "fish", "lichen"]


def test_business_contacts_looks_at_the_top_4_cards_and_offers_to_keep_any_of_them():
    game = scenario(player(megacredits=7, hand=["business_contacts"]), player(), deck=TOP_OF_THE_DECK)

    pick(game, "Play Business Contacts (7 MegaCredits)")

    assert game.decision["kind"] == "keep_cards"
    assert game.decision["player"] == 0
    assert labels(game) == ["Keep Fish", "Keep Mine", "Keep Trees", "Keep Birds"]
    assert keeping(game, 0) == {
        "card": "business_contacts",
        "looking_at": ["fish", "mine", "trees", "birds"],
        "kept": [],
        "keep": 2,
        "price": 0,
    }
    assert "Player 1 looks at the top 4 cards of the deck." in game.log


def test_business_contacts_keeps_2_cards_one_at_a_time_and_discards_the_other_2():
    game = scenario(player(hand=["business_contacts"]), player(), deck=TOP_OF_THE_DECK)

    pick(game, "Play Business Contacts")
    pick(game, type="keep_card", card="trees")
    assert labels(game) == ["Keep Fish", "Keep Mine", "Keep Birds"]
    assert keeping(game, 0)["kept"] == ["trees"]
    assert keeping(game, 0)["keep"] == 1
    pick(game, type="keep_card", card="fish")

    assert hand(game, 0) == ["fish", "trees"]
    assert keeping(game, 0) is None
    assert sorted(game.full_view()["discard"]) == ["birds", "mine"]
    assert game.full_view()["deck"][0] == "lichen"
    assert "Player 1 keeps 2 cards and discards 2." in game.log
    assert game.decision["kind"] == "action"


def test_with_only_2_cards_left_to_draw_business_contacts_keeps_both_without_a_decision():
    elsewhere = [card for card in PROJECT_CARDS if card not in ("business_contacts", "mine", "trees")]
    game = scenario(player(hand=["business_contacts"]), player(hand=elsewhere))

    pick(game, "Play Business Contacts")

    assert hand(game, 0) == ["mine", "trees"]
    assert game.full_view()["discard"] == []
    assert "Player 1 keeps 2 cards and discards 0." in game.log
    assert game.decision["kind"] == "action"


def test_with_only_1_card_left_to_draw_business_contacts_keeps_it_without_a_decision():
    elsewhere = [card for card in PROJECT_CARDS if card not in ("business_contacts", "mine")]
    game = scenario(player(hand=["business_contacts"]), player(hand=elsewhere))

    pick(game, "Play Business Contacts")

    assert hand(game, 0) == ["mine"]
    assert "Player 1 looks at the top card of the deck." in game.log
    assert "Player 1 keeps 1 card and discards 0." in game.log
    assert game.decision["kind"] == "action"


def test_when_the_deck_runs_out_business_contacts_takes_the_rest_from_the_reshuffled_discard_pile():
    # 2 cards in the deck and 3 in the discard pile: the look takes both, then 2 of the reshuffled 3.
    deck, discarded = ["mine", "trees"], ["birds", "fish", "lichen"]
    elsewhere = [card for card in PROJECT_CARDS if card not in ("business_contacts", *deck, *discarded)]
    game = scenario(player(hand=["business_contacts"]), player(hand=elsewhere), deck=deck, discard=discarded)

    pick(game, "Play Business Contacts")

    looking_at = keeping(game, 0)["looking_at"]
    assert len(looking_at) == 4
    assert {"mine", "trees"} <= set(looking_at)
    assert "The deck has run out, so the discard pile is shuffled into a new deck of 3 cards." in game.log
    assert len(game.full_view()["deck"]) == 1
    assert game.full_view()["discard"] == []


def test_business_contacts_earth_tag_stops_counting_once_it_is_played():
    game = scenario(player(hand=["business_contacts"]), player(), deck=TOP_OF_THE_DECK)

    pick(game, "Play Business Contacts")
    pick(game, type="keep_card", card="trees")
    pick(game, type="keep_card", card="fish")

    assert player_board(game, 0)["tags"]["earth"] == 0


def test_business_contacts_has_no_victory_points():
    game = scenario(player(played_cards=["business_contacts"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
