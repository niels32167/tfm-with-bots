"""#192 Invention Contest (2 MegaCredits, Event and science Tags): look at the top 3 cards from the
deck. Take 1 of them into hand and discard the other 2."""

from tests.helpers import final_scores, hand, keeping, labels, pick, player, resources, scenario, terraformed_mars


def test_invention_contest_keeps_1_of_the_top_3_cards_and_discards_the_other_2():
    game = scenario(
        player(megacredits=2, hand=["invention_contest"]), player(), deck=["mine", "trees", "birds", "fish"]
    )

    pick(game, "Play Invention Contest (2 MegaCredits)")
    assert game.decision["kind"] == "keep_cards"
    assert labels(game) == ["Keep Mine", "Keep Trees", "Keep Birds"]
    assert keeping(game, 0) == {
        "card": "invention_contest",
        "looking_at": ["mine", "trees", "birds"],
        "kept": [],
        "keep": 1,
    }
    pick(game, "Keep Birds")

    assert hand(game, 0) == ["birds"]
    assert sorted(game.full_view()["discard"]) == ["mine", "trees"]
    assert resources(game, 0)["megacredits"] == 0
    assert "Player 1 looks at the top 3 cards of the deck." in game.log
    assert "Player 1 keeps 1 card and discards 2." in game.log
    assert game.decision["kind"] == "action"


def test_invention_contest_has_no_victory_points():
    game = scenario(player(played_cards=["invention_contest"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
