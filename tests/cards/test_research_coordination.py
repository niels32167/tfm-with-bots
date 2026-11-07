"""#P40 Research Coordination (Prelude's Project Card, 4 MegaCredits, wild Tag): after being played, when you perform
an action, the wild tag counts as any tag of your choice. The wild Tag's rules are in tests/rules/test_wild_tag.py."""

from tests.helpers import final_scores, offered, pick, player, player_board, production, scenario, terraformed_mars


def test_research_coordination_costs_4_megacredits_and_gives_a_wild_tag():
    game = scenario(player(megacredits=4, hand=["research_coordination"]), player(), prelude=True)

    pick(game, "Play Research Coordination (4 MegaCredits)")

    assert player_board(game, 0)["tags"]["wild"] == 1


def test_its_wild_tag_counts_for_a_tag_requirement():
    # Gene Repair needs 3 science Tags; Research has 2.
    game = scenario(
        player(megacredits=12, hand=["gene_repair"], played_cards=["research", "research_coordination"]),
        player(),
        prelude=True,
    )

    assert offered(game, "Play Gene Repair")


def test_its_wild_tag_sets_off_no_trigger():
    game = scenario(
        player(megacredits=4, hand=["research_coordination"], corporation="saturn_systems"), player(), prelude=True
    )

    pick(game, "Play Research Coordination")

    assert production(game, 0)["megacredits"] == 0


def test_research_coordination_is_worth_no_victory_points():
    game = scenario(player(played_cards=["research_coordination"]), player(), prelude=True, **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
