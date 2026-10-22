"""What each Player may see (the Player View), and the full view for Hotseat and the dev panel."""

from tests.helpers import player, scenario


def test_the_full_view_belongs_to_no_single_player():
    game = scenario(player(), player(), player())

    assert game.full_view()["viewer"] is None
    assert game.player_view(1)["viewer"] == 1


def test_until_there_is_hidden_information_the_full_view_shows_what_every_player_view_shows():
    game = scenario(player(megacredits=30), player(megacredits=5, terraform_rating=24), first_player=1)

    full_view = game.full_view()

    for viewer in (0, 1):
        assert full_view == {**game.player_view(viewer), "viewer": None}
