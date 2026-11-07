"""#P28 Research Network (Prelude Card, wild Tag): increase your MegaCredit Production 1 step. Draw 3 cards. The
wild Tag's rules are in tests/rules/test_wild_tag.py."""

from tests.helpers import hand, player, player_board, production, scenario


def test_research_network_raises_megacredit_production_1_step_and_draws_3_cards():
    game = scenario(player(prelude_cards=["research_network"]), player(), prelude=True,
                    deck=["mine", "trees", "birds", "comet"])

    assert production(game, 0)["megacredits"] == 1
    assert hand(game, 0) == ["mine", "trees", "birds"]
    assert player_board(game, 0)["tags"]["wild"] == 1


def test_its_wild_tag_sets_off_no_trigger():
    game = scenario(player(prelude_cards=["research_network"], corporation="saturn_systems"), player(),
                    prelude=True)

    # Saturn Systems raises its MegaCredit Production for each jovian Tag played; the wild Tag isn't one.
    assert production(game, 0)["megacredits"] == 1
