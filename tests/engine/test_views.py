"""What each Player may see (the Player View), and the full view for Hotseat and the dev panel."""

from tests.helpers import player, scenario


def test_the_full_view_belongs_to_no_single_player():
    game = scenario(player(), player(), player())

    assert game.full_view()["viewer"] is None
    assert game.player_view(1)["viewer"] == 1


def test_a_player_sees_their_own_hand_and_only_the_size_of_anyone_elses():
    game = scenario(player(hand=["mine", "trees"]), player(hand=["grass"], played_cards=["windmills"]))

    boards = game.player_view(0)["players"]

    assert (boards[0]["hand"], boards[0]["hand_size"]) == (["mine", "trees"], 2)
    assert (boards[1]["hand"], boards[1]["hand_size"]) == (None, 1)
    assert boards[1]["played_cards"] == ["windmills"]


def test_the_full_view_shows_every_hand_and_the_deck_order_and_otherwise_what_every_player_view_shows():
    game = scenario(player(megacredits=30, hand=["mine"]), player(hand=["grass"]), first_player=1, deck=["trees"])

    full_view = game.full_view()

    assert [board["hand"] for board in full_view["players"]] == [["mine"], ["grass"]]
    assert full_view["deck"][0] == "trees"
    for viewer in (0, 1):
        own_view = game.player_view(viewer)
        assert own_view["deck"] is None
        for index, board in enumerate(own_view["players"]):
            board["hand"] = full_view["players"][index]["hand"]
        assert full_view == {**own_view, "viewer": None, "deck": full_view["deck"]}
