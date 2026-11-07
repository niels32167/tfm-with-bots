"""Cost changes: discounts, what steel and titanium are worth, Requirement steps, and Events that
change the next card played (see "Discounts" and the notes after it in docs/rules-notes.md)."""

import tm_engine

from tests.helpers import labels, offered, pick, player, player_board, scenario

CATALOG = tm_engine.card_catalog()


def test_discounts_add_up():
    played = ["research_outpost", "earth_catapult", "earth_office"]
    game = scenario(player(megacredits=0, hand=["sponsors", "mine"], played_cards=played), player())

    assert offered(game, "Play Sponsors (0 MegaCredits)")
    assert not offered(game, "Play Mine")
    assert player_board(game, 0)["card_costs"] == {"mine": 1, "sponsors": 0}


def test_indentured_workers_adds_to_the_discounts_of_played_cards():
    game = scenario(
        player(megacredits=0, hand=["indentured_workers", "satellites"], played_cards=["space_station"]), player()
    )

    pick(game, "Play Indentured Workers")

    assert offered(game, "Play Satellites (0 MegaCredits)")


def test_steel_pays_towards_the_discounted_cost():
    game = scenario(player(megacredits=2, steel=1, hand=["mine"], played_cards=["earth_catapult"]), player())

    pick(game, "Play Mine (2 MegaCredits)")

    assert labels(game) == ["Pay 2 MegaCredits", "Pay 1 steel"]


def test_a_discount_makes_neither_a_standard_project_nor_a_cards_action_cheaper():
    played = ["earth_catapult", "research_outpost", "water_import_from_europa"]
    game = scenario(player(megacredits=11, played_cards=played), player())

    assert offered(game, "Power Plant (11 MegaCredits)")
    assert not offered(game, "Asteroid")
    assert not offered(game, "Use the action of Water Import from Europa")


def test_no_card_has_two_tags_a_discount_per_card_counts_so_it_is_the_same_as_one_per_tag():
    """Only Cheung Shing Mars' and Valley Trust's discounts are printed per Tag ("when you play a science tag, you
    pay 2 MC less for it"), and Research has 2 science Tags (tests/cards/test_valley_trust.py)."""
    discounts = [card["effects"]["discount"] for card in CATALOG if "discount" in card.get("effects", {})]
    discounted = {discount.get("tag") for discount in discounts if not discount.get("per_tag")}
    for card in CATALOG:
        for tag in discounted - {None}:
            assert card["tags"].count(tag) <= 1, card["name"]


def test_only_active_cards_and_corporations_change_costs_for_good_and_only_events_change_the_next_card():
    """A Prelude Card's `next_card` changes the card it plays from the hand (Excentric Sponsor)."""
    for card in CATALOG:
        effects = card.get("effects", {})
        if {"discount", "cube_values", "requirement_steps"} & effects.keys():
            assert card["type"] in ("active", "corporation"), card["name"]
        if "next_card" in effects:
            assert card["type"] in ("event", "prelude"), card["name"]
