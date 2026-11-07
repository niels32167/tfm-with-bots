"""#P12 Experimental Forest (Prelude Card): place 1 Greenery Tile. Reveal cards until you reveal two cards with
plant Tags on them. Take them into your hand and discard the rest."""

from tests.helpers import (
    area,
    everything_but,
    hand,
    pick,
    player,
    player_board,
    scenario,
)


def test_experimental_forest_places_a_greenery_then_takes_the_first_2_cards_with_a_plant_tag_revealed():
    game = scenario(
        player(prelude_cards=["experimental_forest"]),
        player(),
        prelude=True,
        deck=["mine", "trees", "asteroid", "lichen", "birds"],
    )

    assert game.decision["kind"] == "area"
    assert hand(game, 0) == []
    pick(game, area="C3")

    assert area(game, "C3")["tile"] == {"type": "greenery", "owner": 0}
    assert game.full_view()["oxygen"] == 1
    assert player_board(game, 0)["terraform_rating"] == 21
    assert hand(game, 0) == ["trees", "lichen"]
    assert game.full_view()["discard"] == ["asteroid", "mine"]
    assert player_board(game, 0)["tags"]["plant"] == 1
    assert game.decision["kind"] == "action"


def test_with_fewer_than_2_cards_with_a_plant_tag_left_it_takes_those_there_are():
    game = scenario(
        player(prelude_cards=["experimental_forest"]),
        player(hand=everything_but("mine", "trees")),
        prelude=True,
        deck=["mine", "trees"],
    )
    pick(game, area="C3")

    assert hand(game, 0) == ["trees"]
    assert game.full_view()["discard"] == ["mine"]
    assert game.decision["kind"] == "action"
