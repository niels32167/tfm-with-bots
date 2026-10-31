"""#073 Mars University (Corporate Era, 8 MegaCredits, building and science Tags, 1 Victory Point):
Effect: when you play a Science tag, including this, you may discard a card from hand to draw a
card."""

from tests.helpers import (
    final_scores,
    hand,
    labels,
    offered,
    pick,
    player,
    scenario,
    terraformed_mars,
)


def test_mars_university_has_no_requirements_and_sets_itself_off():
    game = scenario(player(megacredits=8, hand=["mars_university", "mine"]), player(), deck=["sponsors"])

    pick(game, "Play Mars University (8 MegaCredits)")

    assert game.decision["kind"] == "discard_to_draw"
    assert game.decision["player"] == 0
    assert labels(game) == ["Discard Mine to draw a card", "Done"]
    assert offered(game, type="discard_card", card="mine")


def test_discarding_with_mars_university_puts_the_card_face_down_on_the_discard_pile_and_draws_one():
    game = scenario(player(megacredits=8, hand=["mars_university", "mine"]), player(), deck=["sponsors"])

    pick(game, "Play Mars University")
    pick(game, "Discard Mine to draw a card")

    assert hand(game, 0) == ["sponsors"]
    assert game.full_view()["discard"] == ["mine"]
    assert "Player 1 discards a card to draw one." in game.log
    assert game.decision["kind"] == "action"
    assert offered(game, "End Turn")


def test_with_mars_university_the_player_may_keep_their_hand():
    game = scenario(player(megacredits=8, hand=["mars_university", "mine"]), player(), deck=["sponsors"])

    pick(game, "Play Mars University")
    pick(game, "Done")

    assert hand(game, 0) == ["mine"]
    assert offered(game, "End Turn")


def test_with_an_empty_hand_mars_university_offers_nothing():
    game = scenario(player(megacredits=8, hand=["mars_university"]), player())

    pick(game, "Play Mars University")

    assert game.decision["kind"] == "action"


def test_mars_university_is_set_off_once_for_each_science_tag_so_twice_by_research():
    holding = player(megacredits=11, hand=["research", "mine"], played_cards=["mars_university"])
    game = scenario(holding, player(), deck=["sponsors", "satellites", "lichen", "bushes"])

    pick(game, "Play Research")
    # Research draws its 2 cards first, then the two discards follow.
    assert sorted(hand(game, 0)) == ["mine", "satellites", "sponsors"]
    assert game.decision["kind"] == "discard_to_draw"
    pick(game, "Discard Mine")
    assert game.decision["kind"] == "discard_to_draw"
    pick(game, "Done")

    assert game.decision["kind"] == "action"
    assert sorted(hand(game, 0)) == sorted(["sponsors", "satellites", "lichen"])


def test_mars_university_is_set_off_by_an_event_with_a_science_tag():
    holding = player(megacredits=4, hand=["special_design", "mine"], played_cards=["mars_university"])
    game = scenario(holding, player())

    pick(game, "Play Special Design")

    assert game.decision["kind"] == "discard_to_draw"


def test_mars_university_is_not_set_off_by_a_card_without_a_science_tag_or_another_players_science_tag():
    game = scenario(player(megacredits=4, hand=["mine", "sponsors"], played_cards=["mars_university"]), player())
    other = scenario(player(megacredits=11, hand=["research"]), player(hand=["mine"], played_cards=["mars_university"]))

    pick(game, "Play Mine")
    pick(other, "Play Research")

    assert game.decision["kind"] == "action"
    assert other.decision["kind"] == "action"
    assert other.decision["player"] == 0


def test_mars_university_comes_after_the_cards_tiles():
    # Research Outpost places its City first.
    holding = player(megacredits=18, hand=["research_outpost", "mine"], played_cards=["mars_university"])
    game = scenario(holding, player())

    pick(game, "Play Research Outpost")
    assert game.decision["kind"] == "area"
    pick(game, area="J1")

    assert game.decision["kind"] == "discard_to_draw"


def test_mars_university_is_worth_1_victory_point():
    game = scenario(player(played_cards=["mars_university"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [1, 0]
