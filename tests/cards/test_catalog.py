"""The card catalog: the printed data of the base box's cards (ADR 0003) and Prelude's (ADR 0011),
read through the engine module, which builds in the card file imported from the fan-made card
list (ADR 0005)."""

import re

import pytest
import tm_engine


def in_the_base_box() -> list[dict]:
    return [card for card in tm_engine.card_catalog() if card["expansion"] == "base"]


def in_prelude() -> list[dict]:
    return [card for card in tm_engine.card_catalog() if card["expansion"] == "prelude"]


def project_cards() -> list[dict]:
    return [card for card in in_the_base_box() if card["type"] != "corporation"]


def corporations() -> list[dict]:
    return [card for card in in_the_base_box() if card["type"] == "corporation"]


def test_the_catalog_has_the_208_project_cards_in_number_order_71_of_them_corporate_era():
    cards = project_cards()

    assert [card["number"] for card in cards] == list(range(1, 209))
    assert sum(not card["corporate_era"] for card in cards) == 137
    assert sum(card["corporate_era"] for card in cards) == 71
    assert {card["type"] for card in cards} == {"automated", "active", "event"}


def test_the_catalog_has_the_12_corporations_of_the_base_game_and_corporate_era():
    assert [(card["name"], card["corporate_era"]) for card in corporations()] == [
        ("CrediCor", False),
        ("EcoLine", False),
        ("Helion", False),
        ("Mining Guild", False),
        ("Interplanetary Cinematics", False),
        ("Inventrix", False),
        ("PhoboLog", False),
        ("Tharsis Republic", False),
        ("Thorgate", False),
        ("United Nations Mars Initiative", False),
        ("Teractor", True),
        ("Saturn Systems", True),
    ]
    assert all(card["number"] is None and card["cost"] is None for card in corporations())


def test_every_card_has_its_own_snake_case_id():
    ids = [card["id"] for card in tm_engine.card_catalog()]

    assert len(set(ids)) == len(ids) == 267
    assert all(re.fullmatch(r"[a-z0-9]+(_[a-z0-9]+)*", card_id) for card_id in ids)


def test_the_catalog_has_preludes_35_prelude_cards_after_all_the_others():
    prelude_cards = [card for card in tm_engine.card_catalog() if card["type"] == "prelude"]

    assert tm_engine.card_catalog()[-35:] == prelude_cards
    assert [card["number"] for card in prelude_cards] == list(range(1, 36))
    assert sorted(card["name"] for card in prelude_cards) == [
        "Acquired Space Agency",
        "Allied Banks",
        "Aquifer Turbines",
        "Biofuels",
        "Biolab",
        "Biosphere Support",
        "Business Empire",
        "Dome Farming",
        "Donation",
        "Early Settlement",
        "Ecology Experts",
        "Excentric Sponsor",
        "Experimental Forest",
        "Galilean Mining",
        "Great Aquifer",
        "Huge Asteroid",
        "Io Research Outpost",
        "Loan",
        "Martian Industries",
        "Metal-Rich Asteroid",
        "Metals Company",
        "Mining Operations",
        "Mohole",
        "Mohole Excavation",
        "Nitrogen Shipment",
        "Orbital Construction Yard",
        "Polar Industries",
        "Power Generation",
        "Research Network",
        "Self-Sufficient Settlement",
        "Smelting Plant",
        "Society Support",
        "Supplier",
        "Supply Drop",
        "UNMI Contractor",
    ]
    assert all(card["cost"] is None and card["requirements"] == [] for card in prelude_cards)


def test_the_catalog_has_preludes_project_cards_and_corporations_after_the_base_box():
    assert len(in_the_base_box()) == 220
    assert tm_engine.card_catalog()[:220] == in_the_base_box()
    assert [(card["name"], card["number"], card["type"]) for card in in_prelude()[:12]] == [
        ("House Printing", 36, "automated"),
        ("Lava Tube Settlement", 37, "automated"),
        ("Martian Survey", 38, "event"),
        ("Psychrophiles", 39, "active"),
        ("Research Coordination", 40, "automated"),
        ("SF Memorial", 41, "automated"),
        ("Space Hotels", 42, "automated"),
        ("Cheung Shing Mars", None, "corporation"),
        ("Point Luna", None, "corporation"),
        ("Robinson Industries", None, "corporation"),
        ("Valley Trust", None, "corporation"),
        ("Vitor", None, "corporation"),
    ]
    assert not any(card["corporate_era"] for card in in_prelude())


def card(card_id: str) -> dict:
    [found] = [card for card in tm_engine.card_catalog() if card["id"] == card_id]
    return found


# Cards of every type and kind of Requirement and Victory Points, as printed.
@pytest.mark.parametrize(
    ("card_id", "printed"),
    [
        (
            "colonizer_training_camp",
            {"number": 1, "type": "automated", "corporate_era": False, "cost": 8, "tags": ["building", "jovian"],
             "requirements": [{"type": "oxygen", "max": 5}], "victory_points": 2},
        ),
        (
            "search_for_life",
            {"number": 5, "type": "active", "corporate_era": False, "cost": 3, "tags": ["science"],
             "requirements": [{"type": "oxygen", "max": 6}],
             "victory_points": {"points": 3, "at_least": 1, "of": {"card_resource": "science"}}},
        ),
        (
            "capital",
            {"number": 8, "type": "automated", "corporate_era": False, "cost": 26, "tags": ["building", "city"],
             "requirements": [{"type": "oceans", "min": 4}],
             "victory_points": {"points": 1, "per": 1, "of": {"adjacent": "ocean"}}},
        ),
        (
            "asteroid",
            {"number": 9, "type": "event", "corporate_era": False, "cost": 14, "tags": ["event", "space"],
             "requirements": [], "victory_points": None},
        ),
        (
            "interstellar_colony_ship",
            {"number": 27, "type": "event", "corporate_era": True, "cost": 24, "tags": ["event", "space", "earth"],
             "requirements": [{"type": "tag", "tag": "science", "min": 5}], "victory_points": 4},
        ),
        (
            "ants",
            {"number": 35, "type": "active", "corporate_era": False, "cost": 9, "tags": ["microbe"],
             "requirements": [{"type": "oxygen", "min": 4}],
             "victory_points": {"points": 1, "per": 2, "of": {"card_resource": "microbe"}}},
        ),
        (
            "mine",
            {"number": 56, "type": "automated", "corporate_era": True, "cost": 4, "tags": ["building"],
             "requirements": [], "victory_points": None},
        ),
        (
            "ecological_zone",
            {"number": 128, "type": "active", "corporate_era": False, "cost": 12, "tags": ["plant", "animal"],
             "requirements": [{"type": "tiles", "tile": "greenery", "owner": "you", "min": 1}],
             "victory_points": {"points": 1, "per": 2, "of": {"card_resource": "animal"}}},
        ),
        (
            "advanced_ecosystems",
            {"number": 135, "type": "automated", "corporate_era": False, "cost": 11,
             "tags": ["animal", "microbe", "plant"],
             "requirements": [{"type": "tag", "tag": "plant", "min": 1}, {"type": "tag", "tag": "microbe", "min": 1},
                              {"type": "tag", "tag": "animal", "min": 1}],
             "victory_points": 3},
        ),
        (
            "rad_suits",
            {"number": 186, "type": "automated", "corporate_era": True, "cost": 6, "tags": [],
             "requirements": [{"type": "tiles", "tile": "city", "owner": "anyone", "min": 2}], "victory_points": 1},
        ),
        (
            "immigration_shuttles",
            {"number": 198, "type": "automated", "corporate_era": False, "cost": 31, "tags": ["space", "earth"],
             "requirements": [], "victory_points": {"points": 1, "per": 3, "of": {"tiles_in_play": "city"}}},
        ),
        (
            "mining_guild",
            {"number": None, "type": "corporation", "corporate_era": False, "cost": None,
             "tags": ["building", "building"], "requirements": [], "victory_points": None},
        ),
        (
            "teractor",
            {"number": None, "type": "corporation", "corporate_era": True, "cost": None, "tags": ["earth"],
             "requirements": [], "victory_points": None},
        ),
        (
            "martian_survey",
            {"number": 38, "type": "event", "expansion": "prelude", "cost": 9, "tags": ["event", "science"],
             "requirements": [{"type": "oxygen", "max": 4}], "victory_points": 1},
        ),
        (
            "psychrophiles",
            {"number": 39, "type": "active", "expansion": "prelude", "cost": 2, "tags": ["microbe"],
             "requirements": [{"type": "temperature", "max": -20}], "victory_points": None},
        ),
        (
            "research_coordination",
            {"number": 40, "type": "automated", "expansion": "prelude", "cost": 4, "tags": ["wild"],
             "requirements": [], "victory_points": None},
        ),
        (
            "space_hotels",
            {"number": 42, "type": "automated", "expansion": "prelude", "cost": 12, "tags": ["space", "earth"],
             "requirements": [{"type": "tag", "tag": "earth", "min": 2}], "victory_points": None},
        ),
        (
            "point_luna",
            {"number": None, "type": "corporation", "expansion": "prelude", "cost": None, "tags": ["space", "earth"],
             "requirements": [], "victory_points": None},
        ),
        (
            "ecology_experts",
            {"number": 10, "type": "prelude", "expansion": "prelude", "cost": None, "tags": ["microbe", "plant"],
             "requirements": [], "victory_points": None},
        ),
        (
            "research_network",
            {"number": 28, "type": "prelude", "expansion": "prelude", "cost": None, "tags": ["wild"],
             "requirements": [], "victory_points": None},
        ),
        (
            "donation",
            {"number": 8, "type": "prelude", "expansion": "prelude", "cost": None, "tags": [],
             "requirements": [], "victory_points": None},
        ),
    ],
)
def test_a_card_has_its_printed_data(card_id, printed):
    assert {field: card(card_id)[field] for field in printed} == printed


def test_a_card_has_its_printed_text_and_its_face_for_the_gui():
    nuclear_power = card("nuclear_power")
    text = "(Decrease your MC production 2 steps and increase your Energy production 3 steps.)"

    assert nuclear_power["text"] == text
    parts = [part for part in nuclear_power["face"]["content"]["children"] if part != " "]
    assert [part["class"] for part in parts] == ["production-box production-box-size3a", "description"]
    assert parts[-1]["children"] == [f" {text} "]


def test_a_corporations_text_gives_its_starting_megacredits_and_first_action():
    assert card("valley_trust")["text"] == (
        "(Effect: When you play an Science tag, you pay 2MC less for it.)\n"
        "(You start with 37 MC. As your first action, draw 3 Prelude cards, and play one of them. "
        "Discard the other two.)"
    )
    assert card("vitor")["text"] == (
        "(Effect: When you play a card with a NON-NEGATIVE VP icon, including this, gain 3MC.)\n"
        "(You start with 45 MC. As your first action, fund an award for free.)"
    )


def test_names_are_in_title_case_where_the_card_list_slipped():
    assert card("underground_city")["name"] == "Underground City"
    assert card("anti_gravity_technology")["name"] == "Anti-Gravity Technology"
    assert card("metal_rich_asteroid")["name"] == "Metal-Rich Asteroid"
    assert card("psychrophiles")["name"] == "Psychrophiles"
    assert card("sf_memorial")["name"] == "SF Memorial"


def test_names_are_spelled_as_printed_not_as_other_sources_spell_them():
    assert card("excentric_sponsor")["name"] == "Excentric Sponsor"  # the open-source game has Eccentric
    assert card("allied_banks")["name"] == "Allied Banks"  # the open-source game and Recorded Games have Allied Bank


def test_changing_the_catalog_read_from_the_engine_changes_no_later_read():
    catalog = tm_engine.card_catalog()
    cost = catalog[0]["cost"]
    catalog[0]["cost"] = cost + 1

    assert tm_engine.card_catalog()[0]["cost"] == cost
