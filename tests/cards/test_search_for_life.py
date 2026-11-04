"""#005 Search for Life (3 MegaCredits, science Tag, Oxygen 6 % or less): Action: spend 1 MegaCredit
to reveal the top card of the deck. If it has a microbe Tag, add a science to this card. 3 Victory
Points if there is at least 1 science on this card."""

from tests.helpers import (
    PROJECT_CARDS,
    card_resources,
    final_scores,
    offered,
    pick,
    player,
    resources,
    scenario,
    terraformed_mars,
)


def test_search_for_life_needs_6_percent_oxygen_or_less():
    hand = player(megacredits=3, hand=["search_for_life"])

    assert offered(scenario(hand, player(), oxygen=6), "Play Search for Life")
    assert not offered(scenario(hand, player(), oxygen=7), "Play Search for Life")


def test_revealing_a_card_with_a_microbe_tag_adds_a_science_and_discards_the_card():
    game = scenario(
        player(played_cards=["search_for_life"]), player(), deck=["tardigrades", "mine"]
    )

    pick(game, "Use the action of Search for Life")

    assert resources(game, 0)["megacredits"] == 41
    assert card_resources(game, 0) == {"search_for_life": 1}
    assert game.full_view()["discard"] == ["tardigrades"]
    assert game.full_view()["deck"][0] == "mine"
    assert (
        "Player 1 reveals Tardigrades from the top of the deck and discards it."
        in game.log
    )
    assert "Player 1 adds 1 science to Search for Life." in game.log
    assert game.decision["kind"] == "action"


def test_revealing_a_card_without_a_microbe_tag_adds_nothing_and_the_megacredit_is_spent():
    game = scenario(player(played_cards=["search_for_life"]), player(), deck=["mine"])

    pick(game, "Use the action of Search for Life")

    assert resources(game, 0)["megacredits"] == 41
    assert card_resources(game, 0) == {"search_for_life": 0}
    assert game.full_view()["discard"] == ["mine"]


def test_the_action_needs_a_megacredit():
    game = scenario(player(megacredits=0, played_cards=["search_for_life"]), player())

    assert not offered(game, "Use the action of Search for Life")


def test_the_action_may_be_used_again_after_finding_life():
    holding = player(
        played_cards=["search_for_life"], card_resources={"search_for_life": 1}
    )
    game = scenario(holding, player(), deck=["tardigrades"])

    pick(game, "Use the action of Search for Life")

    assert card_resources(game, 0) == {"search_for_life": 2}


def test_the_discard_pile_is_shuffled_into_the_deck_if_it_has_run_out():
    every_other_card = [
        card for card in PROJECT_CARDS if card not in ("search_for_life", "tardigrades")
    ]
    game = scenario(
        player(played_cards=["search_for_life"], hand=every_other_card),
        player(),
        discard=["tardigrades"],
    )

    pick(game, "Use the action of Search for Life")

    assert card_resources(game, 0) == {"search_for_life": 1}
    assert game.full_view()["discard"] == ["tardigrades"]


def test_the_action_is_not_offered_with_no_card_left_to_reveal():
    every_other_card = [card for card in PROJECT_CARDS if card != "search_for_life"]
    game = scenario(
        player(played_cards=["search_for_life"], hand=every_other_card), player()
    )

    assert not offered(game, "Use the action of Search for Life")


def test_search_for_life_scores_3_victory_points_with_one_science_or_more():
    for science, points in ((0, 0), (1, 3), (5, 3)):
        holding = player(
            played_cards=["search_for_life"],
            card_resources={"search_for_life": science},
        )

        assert (
            final_scores(scenario(holding, player(), **terraformed_mars()))[0]["cards"]
            == points
        )
