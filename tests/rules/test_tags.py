"""Tag counting: a Player's Tags in play are those on their played Automated and Active cards.
Events lie face down once played, so none of their Tags count, the Event Tag included (see
docs/rules-notes.md). Requirements, Milestones, Awards and card Victory Points all count Tags
this one way."""

from tests.helpers import TAGS_THAT_COUNT, player, player_board, scenario

NO_TAGS = dict.fromkeys(TAGS_THAT_COUNT, 0)


def test_a_player_board_counts_the_tags_on_played_automated_and_active_cards():
    # Mine has a building Tag, Power Plant building and power, Development Center (Active)
    # building and science.
    game = scenario(player(played_cards=["mine", "power_plant", "development_center"]), player())

    assert player_board(game, 0)["tags"] == {**NO_TAGS, "building": 3, "power": 1, "science": 1}
    assert player_board(game, 1)["tags"] == NO_TAGS


def test_no_tag_on_a_played_event_counts_not_even_the_event_tag():
    # Technology Demonstration has the Event, space and science Tags; Special Design Event and science.
    game = scenario(player(played_cards=["technology_demonstration", "special_design"]), player())

    assert player_board(game, 0)["tags"] == NO_TAGS


def test_tags_in_hand_do_not_count():
    game = scenario(player(hand=["mine", "power_plant"]), player())

    assert player_board(game, 0)["tags"] == NO_TAGS
