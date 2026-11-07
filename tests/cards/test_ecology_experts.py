"""#P10 Ecology Experts (Prelude Card): increase your plant Production 1 step. Play a card from hand, ignoring
global requirements. Playing it is not optional; with no card in hand that could be played that way, Ecology
Experts can't be played, and is discarded for 15 MegaCredits."""

from tests.helpers import (
    card_costs,
    labels,
    offered,
    pick,
    player,
    player_board,
    production,
    resources,
    scenario,
)


def test_ecology_experts_raises_plant_production_then_plays_a_card_ignoring_its_global_requirements():
    game = scenario(player(prelude_cards=["ecology_experts"], hand=["trees", "mine"]), player(), prelude=True)

    assert game.decision["kind"] == "play_card"
    assert labels(game) == ["Play Mine (4 MegaCredits)", "Play Trees (13 MegaCredits)"]
    pick(game, "Play Trees")

    assert player_board(game, 0)["played_cards"] == ["trees"]
    assert production(game, 0)["plants"] == 4
    assert resources(game, 0)["megacredits"] == 42 - 13
    assert player_board(game, 0)["played_prelude_cards"] == ["ecology_experts"]
    assert game.decision["kind"] == "action"


def test_it_ignores_a_global_requirement_on_a_maximum_too():
    game = scenario(player(prelude_cards=["ecology_experts"], hand=["arctic_algae"]), player(), prelude=True,
                    temperature=0)

    pick(game, "Play Arctic Algae")

    assert player_board(game, 0)["played_cards"] == ["arctic_algae"]


def test_its_own_tags_count_for_the_card_it_plays():
    game = scenario(
        player(prelude_cards=["ecology_experts"], hand=["advanced_ecosystems"], played_cards=["birds"]),
        player(),
        prelude=True,
    )

    assert labels(game) == ["Play Advanced Ecosystems (11 MegaCredits)"]


def test_only_the_card_it_plays_ignores_global_requirements():
    game = scenario(player(prelude_cards=["ecology_experts"], hand=["trees", "lichen"]), player(), prelude=True)

    pick(game, "Play Trees")

    assert game.decision["kind"] == "action"
    assert not offered(game, type="play_card", card="lichen")
    assert player_board(game, 0)["next_card"] is None


def test_with_no_card_it_could_play_it_cant_be_played_and_is_discarded_for_15_megacredits():
    tag_requirement = scenario(player(prelude_cards=["ecology_experts"], hand=["gene_repair"]), player(), prelude=True)
    too_dear = scenario(player(prelude_cards=["ecology_experts"], hand=["trees"], megacredits=12), player(),
                        prelude=True)
    empty_hand = scenario(player(prelude_cards=["ecology_experts"]), player(), prelude=True)

    for game, megacredits in [(tag_requirement, 57), (too_dear, 27), (empty_hand, 57)]:
        assert player_board(game, 0)["played_prelude_cards"] == []
        assert production(game, 0)["plants"] == 0
        assert resources(game, 0)["megacredits"] == megacredits
        assert game.decision["kind"] == "action"
    assert card_costs(too_dear, 0) == {"trees": 13}
