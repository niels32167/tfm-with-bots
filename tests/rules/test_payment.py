"""Paying for a card: MegaCredits, plus steel (worth 2) for a card with a building Tag and
titanium (worth 3) for a card with a space Tag. When there is more than one way to pay, a
payment Decision offers each split; steel and titanium may overpay, but only when the last
cube is needed (see docs/rules-notes.md)."""

from tests.helpers import hand, labels, offered, options, pick, played_cards, player, resources, scenario


def test_without_steel_or_titanium_to_use_a_card_is_paid_in_megacredits_with_no_payment_decision():
    game = scenario(player(megacredits=10, titanium=5, hand=["mine"]), player())

    pick(game, "Play Mine")

    assert game.decision["kind"] == "action"
    assert resources(game, 0)["megacredits"] == 6
    assert resources(game, 0)["titanium"] == 5


def test_steel_can_pay_for_a_card_with_a_building_tag_and_each_split_is_an_option():
    game = scenario(player(megacredits=10, steel=5, hand=["mine"]), player())

    pick(game, "Play Mine (4 MegaCredits)")

    assert game.decision["kind"] == "payment"
    assert game.decision["player"] == 0
    assert labels(game) == ["Pay 4 MegaCredits", "Pay 2 MegaCredits and 1 steel", "Pay 2 steel"]
    assert options(game)[1]["details"] == {
        "type": "payment",
        "card": "mine",
        "megacredits": 2,
        "steel": 1,
        "titanium": 0,
    }


def test_the_card_stays_in_the_hand_until_it_is_paid_for():
    game = scenario(player(megacredits=10, steel=5, hand=["mine"]), player())
    pick(game, "Play Mine")
    assert hand(game, 0) == ["mine"]

    pick(game, "Pay 2 MegaCredits and 1 steel")

    assert hand(game, 0) == []
    assert played_cards(game, 0) == ["mine"]
    assert (resources(game, 0)["megacredits"], resources(game, 0)["steel"]) == (8, 4)
    assert "Player 1 plays Mine, paying 2 MegaCredits and 1 steel." in game.log
    assert game.decision["kind"] == "action"


def test_steel_overpays_only_when_the_last_cube_is_needed():
    # Solar Power costs 11: 6 steel pay 12, since 5 pay only 10.
    game = scenario(player(megacredits=1, steel=8, hand=["solar_power"]), player())

    pick(game, "Play Solar Power")

    assert labels(game) == ["Pay 1 MegaCredit and 5 steel", "Pay 6 steel"]


def test_with_only_one_way_to_pay_there_is_no_payment_decision():
    game = scenario(player(megacredits=0, steel=2, hand=["mine"]), player())

    pick(game, "Play Mine")

    assert game.decision["kind"] == "action"
    assert "Player 1 plays Mine, paying 2 steel." in game.log


def test_steel_cannot_pay_for_a_card_without_a_building_tag():
    game = scenario(player(megacredits=12, steel=10, hand=["trees"]), player(), temperature=-4)

    assert not offered(game, "Play Trees")


def test_titanium_can_pay_3_for_a_card_with_a_space_tag():
    # Solar Wind Power costs 11 and has a space Tag but no building Tag.
    game = scenario(player(megacredits=11, steel=4, titanium=4, hand=["solar_wind_power"]), player())

    pick(game, "Play Solar Wind Power")

    assert labels(game) == [
        "Pay 11 MegaCredits",
        "Pay 8 MegaCredits and 1 titanium",
        "Pay 5 MegaCredits and 2 titanium",
        "Pay 2 MegaCredits and 3 titanium",
        "Pay 4 titanium",
    ]


def test_a_card_is_offered_when_steel_or_titanium_make_up_for_missing_megacredits():
    assert offered(scenario(player(megacredits=2, steel=1, hand=["mine"]), player()), "Play Mine")
    assert not offered(scenario(player(megacredits=1, steel=1, hand=["mine"]), player()), "Play Mine")
    assert offered(
        scenario(player(megacredits=0, titanium=4, hand=["solar_wind_power"]), player()), "Play Solar Wind Power"
    )
