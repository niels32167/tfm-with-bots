"""#187 Aquifer Pumping (18 MegaCredits, building Tag): Action: spend 8 MegaCredits to place 1 Ocean
Tile. Steel may be used as if you were playing a building card."""

from tests.helpers import (
    final_scores,
    labels,
    offered,
    pick,
    player,
    player_board,
    resources,
    scenario,
    terraformed_mars,
)


def test_aquifer_pumping_has_no_requirements_and_does_nothing_when_played():
    game = scenario(player(megacredits=18, hand=["aquifer_pumping"]), player())

    pick(game, "Play Aquifer Pumping (18 MegaCredits)")

    assert resources(game, 0)["megacredits"] == 0
    assert game.player_view(0)["oceans"] == 0


def test_steel_may_pay_for_aquifer_pumpings_action_at_2_megacredits_each():
    game = scenario(player(megacredits=8, steel=4, played_cards=["aquifer_pumping"]), player())

    pick(game, "Use the action of Aquifer Pumping")

    assert labels(game) == [
        "Pay 8 MegaCredits",
        "Pay 6 MegaCredits and 1 steel",
        "Pay 4 MegaCredits and 2 steel",
        "Pay 2 MegaCredits and 3 steel",
        "Pay 4 steel",
    ]
    pick(game, "Pay 4 steel")
    assert resources(game, 0)["steel"] == 0
    assert resources(game, 0)["megacredits"] == 8
    pick(game, "Place the Ocean on A2")
    assert game.player_view(0)["oceans"] == 1
    assert player_board(game, 0)["terraform_rating"] == 21


def test_with_only_megacredits_aquifer_pumping_pays_8_without_a_decision():
    game = scenario(player(megacredits=8, played_cards=["aquifer_pumping"]), player())

    pick(game, "Use the action of Aquifer Pumping")

    assert resources(game, 0)["megacredits"] == 0
    assert game.decision["kind"] == "area"


def test_aquifer_pumpings_action_needs_8_megacredits_or_steel_to_make_them_up_and_not_titanium():
    using = player(megacredits=7, titanium=5, played_cards=["aquifer_pumping"])
    assert not offered(scenario(using, player()), type="use_action")
    using = player(megacredits=0, steel=4, played_cards=["aquifer_pumping"])
    assert offered(scenario(using, player()), type="use_action")


def test_aquifer_pumping_has_no_victory_points():
    game = scenario(player(played_cards=["aquifer_pumping"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
