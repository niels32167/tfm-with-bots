"""#071 Advanced Alloys (Corporate Era, 9 MegaCredits, science Tag): Effect: each titanium you have
is worth 1 MegaCredit extra. Each steel you have is worth 1 MegaCredit extra."""

from tests.helpers import final_scores, labels, offered, pick, player, resources, scenario, terraformed_mars


def test_advanced_alloys_has_no_requirements_and_costs_9_megacredits():
    game = scenario(player(megacredits=9, hand=["advanced_alloys"]), player())

    pick(game, "Play Advanced Alloys (9 MegaCredits)")

    assert resources(game, 0)["megacredits"] == 0


def test_with_advanced_alloys_steel_pays_3_megacredits_towards_a_card_with_a_building_tag():
    # Mine costs 4: one steel leaves 1 MegaCredit to pay, and two pay it all.
    game = scenario(player(megacredits=4, steel=2, hand=["mine"], played_cards=["advanced_alloys"]), player())

    pick(game, "Play Mine")

    assert labels(game) == ["Pay 4 MegaCredits", "Pay 1 MegaCredit and 1 steel", "Pay 2 steel"]
    pick(game, "Pay 1 MegaCredit and 1 steel")
    assert resources(game, 0)["megacredits"] == 3
    assert resources(game, 0)["steel"] == 1


def test_with_advanced_alloys_titanium_pays_4_megacredits_towards_a_card_with_a_space_tag():
    # Satellites costs 10: three titanium pay it all.
    holding = player(megacredits=0, titanium=3, hand=["satellites"], played_cards=["advanced_alloys"])
    game = scenario(holding, player())

    assert offered(game, "Play Satellites")
    pick(game, "Play Satellites")
    assert resources(game, 0)["titanium"] == 0
    assert "Player 1 plays Satellites, paying 3 titanium." in game.log


def test_without_advanced_alloys_the_same_cubes_do_not_pay_for_the_card():
    assert not offered(scenario(player(megacredits=0, titanium=3, hand=["satellites"]), player()), "Play Satellites")


def test_with_advanced_alloys_titanium_pays_4_megacredits_towards_water_import_from_europas_action():
    played = ["advanced_alloys", "water_import_from_europa"]
    game = scenario(player(megacredits=12, titanium=3, played_cards=played), player())

    pick(game, "Use the action of Water Import from Europa")

    assert labels(game) == [
        "Pay 12 MegaCredits",
        "Pay 8 MegaCredits and 1 titanium",
        "Pay 4 MegaCredits and 2 titanium",
        "Pay 3 titanium",
    ]


def test_with_advanced_alloys_steel_pays_3_megacredits_towards_aquifer_pumpings_action():
    # Its 8 MegaCredits: 2 steel at 3 each and 2 MegaCredits are the only way to pay them.
    game = scenario(player(megacredits=2, steel=2, played_cards=["advanced_alloys", "aquifer_pumping"]), player())

    pick(game, "Use the action of Aquifer Pumping")

    assert "Player 1 pays 2 MegaCredits and 2 steel." in game.log
    assert resources(game, 0)["megacredits"] == 0
    assert resources(game, 0)["steel"] == 0
    assert game.decision["kind"] == "area"


def test_advanced_alloys_is_worth_no_victory_points():
    game = scenario(player(played_cards=["advanced_alloys"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
