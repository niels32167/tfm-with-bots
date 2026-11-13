"""Names in Recorded Games, mapped to the card catalog's ids and the engine's Milestone and Award ids."""

from ai.recorded_games.names import award_id, card_id, milestone_id


def test_card_names_resolve_to_catalog_ids():
    assert card_id("Earth Catapult") == "earth_catapult"
    assert card_id("Robinson Industries") == "robinson_industries"
    assert card_id("Business Empire") == "business_empire"


def test_spelling_differences_from_the_catalog_resolve():
    assert card_id("Inventors' Guild") == "inventors_guild"
    assert card_id("Permafrost extraction") == "permafrost_extraction"
    assert card_id("Allied Bank") == "allied_banks"
    assert card_id("CEO's Favourite Project") == "ceos_favorite_project"


def test_untranslated_prelude_names_resolve_by_their_number():
    assert card_id("card_prelude_P34") == "unmi_contractor"
    assert card_id("card_prelude_P01") == "allied_banks"


def test_cards_outside_the_catalog_do_not_resolve():
    assert card_id("Begginer Corp") is None
    assert card_id("Venus Governor") is None
    assert card_id("card_prelude_P99") is None


def test_tharsis_milestones_and_awards_resolve_in_english_and_untranslated():
    assert milestone_id("Planner") == "planner"
    assert milestone_id("Terraformer") == "terraformer"
    assert award_id("Thermalist") == "thermalist"
    assert award_id("Bankier") == "banker"


def test_other_maps_milestones_and_awards_do_not_resolve():
    assert milestone_id("Generalist") is None
    assert award_id("Podróżnik") is None


def test_untranslated_polish_award_names_resolve():
    assert [award_id(name) for name in ("Potentat Ziemski", "Bankier", "Naukowiec", "Magnat Cieplny", "Górnik")] == [
        "landlord", "banker", "scientist", "thermalist", "miner",
    ]  # fmt: skip
