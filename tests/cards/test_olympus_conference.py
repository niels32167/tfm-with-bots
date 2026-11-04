"""#185 Olympus Conference (10 MegaCredits, building, earth and science Tags, 1 Victory Point): when
you play a science Tag, including this, either add a science to this card, or remove a science from
this card to draw a card."""

from tests.helpers import (
    PROJECT_CARDS,
    card_resources,
    final_scores,
    hand,
    labels,
    offered,
    pick,
    player,
    scenario,
    terraformed_mars,
)


def test_olympus_conference_sets_itself_off_and_with_no_science_on_it_just_adds_one():
    game = scenario(player(megacredits=10, hand=["olympus_conference"]), player())

    pick(game, "Play Olympus Conference (10 MegaCredits)")

    assert card_resources(game, 0) == {"olympus_conference": 1}
    assert game.decision["kind"] == "action"


def test_with_a_science_on_it_the_player_chooses_between_adding_and_removing_to_draw():
    game = scenario(
        player(
            megacredits=13,
            hand=["regolith_eaters"],
            played_cards=["olympus_conference"],
            card_resources={"olympus_conference": 1},
        ),
        player(),
        deck=["sponsors"],
    )

    pick(game, "Play Regolith Eaters")

    assert game.decision["kind"] == "olympus_conference"
    assert labels(game) == [
        "Add 1 science to Olympus Conference",
        "Remove 1 science from Olympus Conference to draw a card",
    ]
    pick(game, "Remove 1 science")
    assert card_resources(game, 0)["olympus_conference"] == 0
    assert hand(game, 0) == ["sponsors"]
    assert "Player 1 removes 1 science from Olympus Conference." in game.log
    assert "Player 1 draws 1 card." in game.log
    assert game.decision["kind"] == "action"


def test_adding_a_science_draws_nothing():
    game = scenario(
        player(
            megacredits=13,
            hand=["regolith_eaters"],
            played_cards=["olympus_conference"],
            card_resources={"olympus_conference": 2},
        ),
        player(),
    )

    pick(game, "Play Regolith Eaters")
    pick(game, "Add 1 science")

    assert card_resources(game, 0)["olympus_conference"] == 3
    assert hand(game, 0) == []


def test_tags_other_than_science_do_not_set_it_off():
    game = scenario(
        player(megacredits=4, hand=["mine"], played_cards=["olympus_conference"]),
        player(),
    )

    pick(game, "Play Mine")

    assert card_resources(game, 0) == {"olympus_conference": 0}
    assert game.decision["kind"] == "action"


def test_another_players_science_tag_does_not_set_it_off():
    game = scenario(
        player(megacredits=13, hand=["regolith_eaters"]),
        player(played_cards=["olympus_conference"]),
    )

    pick(game, "Play Regolith Eaters")

    assert card_resources(game, 1) == {"olympus_conference": 0}


def test_research_counts_as_2_science_tags_so_it_sets_it_off_twice():
    game = scenario(
        player(megacredits=11, hand=["research"], played_cards=["olympus_conference"]),
        player(),
        deck=["sponsors", "satellites", "lichen"],
    )

    pick(game, "Play Research")

    # With none on it the first adds without a choice; the second is a choice.
    assert game.decision["kind"] == "olympus_conference"
    assert card_resources(game, 0) == {"olympus_conference": 1}
    pick(game, "Remove 1 science")

    assert card_resources(game, 0) == {"olympus_conference": 0}
    assert sorted(hand(game, 0)) == ["lichen", "satellites", "sponsors"]
    assert game.decision["kind"] == "action"


def test_after_removing_the_last_science_a_second_tag_adds_one_without_a_choice():
    game = scenario(
        player(
            megacredits=11,
            hand=["research"],
            played_cards=["olympus_conference"],
            card_resources={"olympus_conference": 1},
        ),
        player(),
    )

    pick(game, "Play Research")
    pick(game, "Remove 1 science")

    assert card_resources(game, 0) == {"olympus_conference": 1}
    assert game.decision["kind"] == "action"


def test_with_no_card_left_to_draw_it_just_adds_a_science():
    every_card = [
        card
        for card in PROJECT_CARDS
        if card not in ("olympus_conference", "regolith_eaters")
    ]
    game = scenario(
        player(
            megacredits=13,
            hand=["regolith_eaters", *every_card],
            played_cards=["olympus_conference"],
            card_resources={"olympus_conference": 1},
        ),
        player(),
    )

    pick(game, "Play Regolith Eaters")

    assert card_resources(game, 0)["olympus_conference"] == 2
    assert game.decision["kind"] == "action"


def both_due(**fields) -> dict:
    """A Player with Olympus Conference, with a science on it, and Mars University in play."""
    return player(
        megacredits=13,
        played_cards=["mars_university", "olympus_conference"],
        card_resources={"olympus_conference": 1},
        **fields,
    )


def test_with_mars_university_the_player_orders_the_two_as_the_options_of_one_decision():
    game = scenario(
        both_due(hand=["regolith_eaters", "mine"]),
        player(),
        deck=["sponsors", "satellites"],
    )

    pick(game, "Play Regolith Eaters")

    assert game.decision["kind"] == "olympus_conference"
    assert labels(game) == [
        "Add 1 science to Olympus Conference",
        "Remove 1 science from Olympus Conference to draw a card",
        "Discard Mine to draw a card",
        "Keep the hand",
    ]


def test_carrying_out_olympus_conference_first_leaves_mars_universitys_discard_with_the_card_drawn():
    game = scenario(
        both_due(hand=["regolith_eaters", "mine"]),
        player(),
        deck=["sponsors", "satellites"],
    )

    pick(game, "Play Regolith Eaters")
    pick(game, "Remove 1 science")

    assert game.decision["kind"] == "discard_to_draw"
    assert labels(game) == [
        "Discard Mine to draw a card",
        "Discard Sponsors to draw a card",
        "Done",
    ]
    pick(game, "Discard Sponsors")
    assert sorted(hand(game, 0)) == ["mine", "satellites"]
    assert game.decision["kind"] == "action"


def test_carrying_out_mars_university_first_leaves_olympus_conferences_choice():
    game = scenario(
        both_due(hand=["regolith_eaters", "mine"]),
        player(),
        deck=["sponsors", "satellites"],
    )

    pick(game, "Play Regolith Eaters")
    pick(game, "Discard Mine")

    assert hand(game, 0) == ["sponsors"]
    assert game.decision["kind"] == "olympus_conference"
    assert labels(game) == [
        "Add 1 science to Olympus Conference",
        "Remove 1 science from Olympus Conference to draw a card",
    ]
    pick(game, "Add 1 science")
    assert card_resources(game, 0)["olympus_conference"] == 2
    assert game.decision["kind"] == "action"


def test_keeping_the_hand_leaves_olympus_conferences_choice():
    game = scenario(both_due(hand=["regolith_eaters", "mine"]), player())

    pick(game, "Play Regolith Eaters")
    pick(game, "Keep the hand")

    assert hand(game, 0) == ["mine"]
    assert game.decision["kind"] == "olympus_conference"


def test_with_an_empty_hand_olympus_conference_comes_first_as_its_draw_gives_mars_university_a_card():
    game = scenario(
        both_due(hand=["regolith_eaters"]), player(), deck=["sponsors", "satellites"]
    )

    pick(game, "Play Regolith Eaters")

    assert labels(game) == [
        "Add 1 science to Olympus Conference",
        "Remove 1 science from Olympus Conference to draw a card",
    ]
    pick(game, "Remove 1 science")
    assert labels(game) == ["Discard Sponsors to draw a card", "Done"]


def test_with_an_empty_hand_and_a_science_added_mars_university_has_nothing_to_discard():
    game = scenario(both_due(hand=["regolith_eaters"]), player())

    pick(game, "Play Regolith Eaters")
    pick(game, "Add 1 science")

    assert game.decision["kind"] == "action"


def test_with_no_science_on_it_olympus_conferences_add_comes_before_mars_universitys_discard():
    game = scenario(
        player(
            megacredits=13,
            hand=["regolith_eaters", "mine"],
            played_cards=["mars_university", "olympus_conference"],
        ),
        player(),
    )

    pick(game, "Play Regolith Eaters")

    assert card_resources(game, 0)["olympus_conference"] == 1
    assert game.decision["kind"] == "discard_to_draw"


def test_its_decision_comes_once_the_card_played_is_done():
    game = scenario(
        both_due(hand=["research"]),
        player(),
        deck=["sponsors", "satellites", "lichen", "bushes"],
    )

    pick(game, "Play Research")

    # Research's own 2 cards are drawn first.
    assert sorted(hand(game, 0)) == ["satellites", "sponsors"]
    assert game.decision["kind"] == "olympus_conference"


def test_olympus_conference_scores_its_fixed_victory_point_whatever_is_on_it():
    for science in (0, 3):
        holding = player(
            played_cards=["olympus_conference"],
            card_resources={"olympus_conference": science},
        )

        assert (
            final_scores(scenario(holding, player(), **terraformed_mars()))[0]["cards"]
            == 1
        )


def test_it_is_a_building_card_for_which_steel_pays():
    game = scenario(
        player(megacredits=0, steel=5, hand=["olympus_conference"]), player()
    )

    assert offered(game, "Play Olympus Conference")
