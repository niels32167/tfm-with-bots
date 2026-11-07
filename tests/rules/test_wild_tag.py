"""Research Network's wild Tag. The Prelude rulebook: "After being played, when you perform an action, the wild
tag is a tag of your choice. This means it does not trigger effects when being put into play, nor does it count
during scoring at the end of the game, but you may use it in an action, for example to help claim a milestone."
Like the open-source game, it counts as one more of whichever Tag is counted for a Requirement, a Milestone or a
card's effect when played, and never for a Trigger, an Award or Victory Points (see docs/rules-notes.md)."""

from tests.helpers import (
    CARDS,
    PROJECT_CARDS,
    award,
    final_scores,
    funded,
    milestone,
    offered,
    pick,
    player,
    player_board,
    production,
    scenario,
    terraformed_mars,
)

WITH_A_WILD_TAG = {"played_prelude_cards": ["research_network"]}
SEVEN_BUILDING_CARDS = [card for card in PROJECT_CARDS if CARDS[card]["tags"] == ["building"]][:7]


def test_it_counts_for_a_tag_requirement():
    with_wild = scenario(player(hand=["gene_repair"], played_cards=["research"], **WITH_A_WILD_TAG), player(), prelude=True)
    without = scenario(player(hand=["gene_repair"], played_cards=["research"]), player(), prelude=True)

    assert offered(with_wild, type="play_card", card="gene_repair")
    assert not offered(without, type="play_card", card="gene_repair")


def test_it_counts_for_a_milestone():
    game = scenario(player(played_cards=SEVEN_BUILDING_CARDS, **WITH_A_WILD_TAG), player(), prelude=True)

    assert milestone(game, "builder")["counts"] == [8, 0]
    pick(game, "Claim the Builder Milestone")
    assert milestone(game, "builder")["claimed_by"] == 0


def test_it_counts_for_an_effect_of_a_card_played_per_tag():
    game = scenario(player(hand=["power_grid"], megacredits=18, **WITH_A_WILD_TAG), player(), prelude=True)

    pick(game, "Play Power Grid")

    assert production(game, 0)["energy"] == 2


def test_it_never_counts_for_an_award():
    game = scenario(player(played_cards=["research"], **WITH_A_WILD_TAG), player(), prelude=True, awards=[funded("scientist", 0)])

    assert award(game, "scientist")["counts"] == [2, 0]


def test_it_never_counts_for_victory_points():
    game = scenario(player(played_cards=["ganymede_colony"], **WITH_A_WILD_TAG), player(), prelude=True, **terraformed_mars())

    assert final_scores(game)[0]["cards"] == 1


def test_the_tags_shown_count_it_apart():
    game = scenario(player(played_cards=["research"], **WITH_A_WILD_TAG), player(), prelude=True)

    tags = player_board(game, 0)["tags"]
    assert (tags["science"], tags["wild"]) == (2, 1)
