"""#012 Water Import from Europa (25 MegaCredits, space and jovian Tags, 1 Victory Point for each
jovian Tag you have): Action: pay 12 MegaCredits to place an Ocean Tile. Titanium may be used as if
playing a space card."""

from tests.helpers import (
    areas_offered,
    final_scores,
    labels,
    ocean,
    offered,
    pick,
    player,
    player_board,
    resources,
    scenario,
    terraformed_mars,
)

NINE_OCEANS = [ocean(area) for area in ("A2", "A4", "A5", "B6", "D8", "E4", "E5", "E6", "F6")]


def test_water_import_from_europa_has_no_requirements_and_does_nothing_when_played():
    game = scenario(player(megacredits=25, hand=["water_import_from_europa"]), player())

    pick(game, "Play Water Import from Europa (25 MegaCredits)")

    assert resources(game, 0)["megacredits"] == 0
    assert game.player_view(0)["oceans"] == 0


def test_water_import_from_europas_action_pays_12_megacredits_to_place_an_ocean():
    game = scenario(player(megacredits=13, played_cards=["water_import_from_europa"]), player())

    pick(game, "Use the action of Water Import from Europa")

    assert resources(game, 0)["megacredits"] == 1
    assert "Player 1 pays 12 MegaCredits." in game.log
    assert game.decision["kind"] == "area"
    assert len(areas_offered(game)) == 12
    pick(game, "Place the Ocean on A2")
    assert game.player_view(0)["oceans"] == 1
    assert player_board(game, 0)["terraform_rating"] == 21
    assert offered(game, "End Turn")


def test_titanium_may_pay_for_water_import_from_europas_action_at_3_megacredits_each():
    game = scenario(player(megacredits=12, titanium=4, played_cards=["water_import_from_europa"]), player())

    pick(game, "Use the action of Water Import from Europa")

    assert game.decision["kind"] == "payment"
    assert labels(game) == [
        "Pay 12 MegaCredits",
        "Pay 9 MegaCredits and 1 titanium",
        "Pay 6 MegaCredits and 2 titanium",
        "Pay 3 MegaCredits and 3 titanium",
        "Pay 4 titanium",
    ]
    assert game.decision["options"][4]["details"] == {
        "type": "payment",
        "card": "water_import_from_europa",
        "action": True,
        "megacredits": 0,
        "steel": 0,
        "titanium": 4,
    }
    pick(game, "Pay 6 MegaCredits and 2 titanium")
    assert resources(game, 0)["megacredits"] == 6
    assert resources(game, 0)["titanium"] == 2
    assert game.decision["kind"] == "area"


def test_water_import_from_europas_action_needs_12_megacredits_or_titanium_to_make_them_up():
    using = player(megacredits=11, steel=5, played_cards=["water_import_from_europa"])
    assert not offered(scenario(using, player()), type="use_action")
    using = player(megacredits=3, titanium=3, played_cards=["water_import_from_europa"])
    assert offered(scenario(using, player()), type="use_action")


def test_once_9_oceans_are_placed_water_import_from_europas_action_is_still_offered_and_places_none():
    game = scenario(player(megacredits=12, played_cards=["water_import_from_europa"]), player(), tiles=NINE_OCEANS)

    pick(game, "Use the action of Water Import from Europa")

    assert resources(game, 0)["megacredits"] == 0
    assert "All 9 Oceans are already placed, so no Ocean is placed." in game.log
    assert game.decision["kind"] == "action"


def test_water_import_from_europa_is_worth_1_victory_point_for_each_jovian_tag_its_own_included():
    alone = scenario(player(played_cards=["water_import_from_europa"]), player(), **terraformed_mars())
    assert [score["cards"] for score in final_scores(alone)] == [1, 0]
    # Io Mining Industries has its own jovian Tag and 1 Victory Point for each.
    with_io = player(played_cards=["water_import_from_europa", "io_mining_industries"])
    game = scenario(with_io, player(), **terraformed_mars())
    assert [score["cards"] for score in final_scores(game)] == [4, 0]
