"""#P16 Io Research Outpost (Prelude Card, jovian and science Tags): increase your titanium Production
1 step. Draw a card."""

from tests.helpers import hand, player, player_board, production, scenario


def test_io_research_outpost_raises_titanium_production_and_draws_a_card():
    game = scenario(player(prelude_cards=["io_research_outpost"]), player(), prelude=True, deck=["mine"])

    assert production(game, 0)["titanium"] == 1
    assert hand(game, 0) == ["mine"]
    tags = player_board(game, 0)["tags"]
    assert (tags["jovian"], tags["science"]) == (1, 1)


def test_its_jovian_tag_sets_off_saturn_systems():
    game = scenario(player(prelude_cards=["io_research_outpost"], corporation="saturn_systems"), player(), prelude=True)

    assert production(game, 0)["megacredits"] == 1
