"""The mismatch report (`uv run python -m tools.card_mismatches`) compares our card file with
the open-source game's card definitions. These tests feed it card definitions written in the
same shape as that game's TypeScript."""

import pytest
import tm_engine

from tools.card_mismatches import (
    CACHE,
    COMMIT,
    REPORT,
    compare,
    corporate_era_classes,
    load_open_source_cards,
    parse_open_source_card,
    report,
)


def project_card(fields: str, *, number: str = "100", name: str = "TEST_CARD", extra: str = "") -> str:
    """An open-source card definition: a class whose constructor passes its data to super()."""
    return f"""
import {{Card}} from '../Card';

export class TestCard extends Card implements IProjectCard {{
  constructor() {{
    super({{
      name: CardName.{name},
      {fields}
      {extra}
      metadata: {{
        cardNumber: '{number}',
        renderData: CardRenderer.builder((b) => {{
          b.production((pb) => pb.energy(1));
        }}),
        victoryPoints: CardRenderDynamicVictoryPoints.jovians(1, 1),
      }},
    }});
  }}
}}
"""


def test_a_project_card_definition_gives_its_number_name_type_cost_tags_requirements_and_victory_points():
    source = project_card(
        "type: CardType.AUTOMATED, tags: [Tag.JOVIAN, Tag.BUILDING], cost: 8, victoryPoints: 2,"
        " requirements: {oxygen: 5, max},",
        number="001",
        name="COLONIZER_TRAINING_CAMP",
    )

    assert parse_open_source_card(source, "ColonizerTrainingCamp.ts") == {
        "number": 1,
        "name": "COLONIZER_TRAINING_CAMP",
        "type": "automated",
        "cost": 8,
        "tags": ["jovian", "building"],
        "requirements": [{"type": "oxygen", "max": 5}],
        "victory_points": 2,
    }


def test_a_card_whose_fields_come_from_its_base_class_and_constructor_arguments():
    base_class = """
export abstract class MiningCard extends Card implements IProjectCard {
  constructor(
    name: CardName,
    cost: number,
    metadata: CardMetadata) {
    super({
      type: CardType.AUTOMATED,
      name,
      tags: [Tag.BUILDING],
      cost,
      metadata,
    });
  }
}
"""
    source = """
export class MiningArea extends MiningCard {
  constructor(
    name = CardName.MINING_AREA,
    metadata = {
      cardNumber: '064',
    }) {
    super(
      name,
      4,
      metadata,
    );
  }
}
"""

    card = parse_open_source_card(source, "MiningArea.ts", base_classes={"MiningCard": base_class})

    assert (card["number"], card["name"], card["cost"], card["tags"]) == (64, "MINING_AREA", 4, ["building"])


def test_a_card_named_and_priced_by_constructor_defaults_without_the_points_drawn_in_its_metadata():
    # The Victory Points in `metadata` only draw the card; those passed to super() count.
    source = """
export class TestCity extends Card implements IProjectCard {
  constructor(
    name = CardName.TEST_CITY,
    cost = 26,
    metadata: CardMetadata = {
      cardNumber: '100',
      victoryPoints: oceans(1, 1),
    },
  ) {
    super({
      type: CardType.AUTOMATED,
      name,
      cost,
      behavior: {tile: {type: TileType.CAPITAL, on: 'city'}},
      metadata,
    });
  }
}
"""

    card = parse_open_source_card(source, "TestCity.ts")

    assert (card["name"], card["cost"], card["tags"], card["requirements"], card["victory_points"]) == (
        "TEST_CITY",
        26,
        [],
        [],
        None,
    )


@pytest.mark.parametrize(
    ("written", "requirements"),
    [
        ("{oxygen: 5}", [{"type": "oxygen", "min": 5}]),
        ("{temperature: -12, max}", [{"type": "temperature", "max": -12}]),
        ("{oceans: 3, max}", [{"type": "oceans", "max": 3}]),
        ("{tag: Tag.SCIENCE, count: 3}", [{"type": "tag", "tag": "science", "min": 3}]),
        ("{tag: Tag.JOVIAN}", [{"type": "tag", "tag": "jovian", "min": 1}]),
        (
            "[{tag: Tag.PLANT}, {tag: Tag.ANIMAL}]",
            [{"type": "tag", "tag": "plant", "min": 1}, {"type": "tag", "tag": "animal", "min": 1}],
        ),
        ("{production: Resource.TITANIUM, count: 1}", [{"type": "production", "resource": "titanium", "min": 1}]),
        ("{greeneries: 1}", [{"type": "tiles", "tile": "greenery", "owner": "you", "min": 1}]),
        ("{cities: 2, all}", [{"type": "tiles", "tile": "city", "owner": "anyone", "min": 2}]),
    ],
)
def test_requirements_are_read_into_the_card_files_own_form(written, requirements):
    source = project_card(f"type: CardType.AUTOMATED, cost: 10, requirements: {written},")

    assert parse_open_source_card(source, "TestCard.ts")["requirements"] == requirements


@pytest.mark.parametrize(
    ("written", "resource_type", "victory_points"),
    [
        ("-2", "", -2),
        (
            "{resourcesHere: {}}",
            "resourceType: CardResource.ANIMAL,",
            {"points": 1, "per": 1, "of": {"card_resource": "animal"}},
        ),
        (
            "{resourcesHere: {}, per: 2}",
            "resourceType: CardResource.MICROBE,",
            {"points": 1, "per": 2, "of": {"card_resource": "microbe"}},
        ),
        (
            "{resourcesHere: {}, each: 2}",
            "resourceType: CardResource.SCIENCE,",
            {"points": 2, "per": 1, "of": {"card_resource": "science"}},
        ),
        ("{tag: Tag.JOVIAN}", "", {"points": 1, "per": 1, "of": {"tag": "jovian"}}),
        ("{oceans: {}, nextToThis: {}}", "", {"points": 1, "per": 1, "of": {"adjacent": "ocean"}}),
        ("{cities: {}, nextToThis: {}}", "", {"points": 1, "per": 1, "of": {"adjacent": "city"}}),
        ("{cities: {}, all: true, per: 3}", "", {"points": 1, "per": 3, "of": {"tiles_in_play": "city"}}),
        ("'special'", "", "special"),
    ],
)
def test_victory_points_are_read_into_the_card_files_own_form(written, resource_type, victory_points):
    source = project_card(f"type: CardType.ACTIVE, cost: 10, {resource_type} victoryPoints: {written},")

    assert parse_open_source_card(source, "TestCard.ts")["victory_points"] == victory_points


def test_a_corporation_is_named_after_its_class_and_has_no_number_or_cost():
    source = """
export class MiningGuild extends CorporationCard {
  constructor() {
    super({
      name: CardName.MINING_GUILD,
      tags: [Tag.BUILDING, Tag.BUILDING],
      startingMegaCredits: 30,
      metadata: {cardNumber: 'R24'},
    });
  }
}
"""

    assert parse_open_source_card(source, "MiningGuild.ts") == {
        "number": None,
        "name": "MINING_GUILD",
        "type": "corporation",
        "cost": None,
        "tags": ["building", "building"],
        "requirements": [],
        "victory_points": None,
        "starting_megacredits": 30,
    }


def test_the_card_manifests_say_which_card_classes_are_corporate_era():
    manifests = """
export const BASE_CARD_MANIFEST = new ModuleManifest({
  module: 'base',
  projectCards: {
    [CardName.ADAPTED_LICHEN]: {Factory: AdaptedLichen},
  },
  corporationCards: {
    [CardName.CREDICOR]: {Factory: CrediCor},
  },
});

export const CORP_ERA_CARD_MANIFEST = new ModuleManifest({
  module: 'corpera',
  projectCards: {
    [CardName.MINE]: {Factory: Mine},
  },
  corporationCards: {
    [CardName.TERACTOR]: {Factory: Teractor},
  },
});
"""

    assert corporate_era_classes(manifests) == {"Mine", "Teractor"}


def test_a_file_that_defines_no_card_is_skipped():
    assert parse_open_source_card("export abstract class MiningCard extends Card {}", "MiningCard.ts") is None


def ours(**fields) -> dict:
    card = {
        "id": "test_card",
        "number": 100,
        "name": "Test Card",
        "type": "automated",
        "corporate_era": False,
        "expansion": "base",
        "cost": 10,
        "tags": [],
        "requirements": [],
        "victory_points": None,
    }
    return {**card, **fields}


def theirs(**fields) -> dict:
    card = {
        "number": 100,
        "name": "TEST_CARD",
        "type": "automated",
        "corporate_era": False,
        "cost": 10,
        "tags": [],
        "requirements": [],
        "victory_points": None,
    }
    return {**card, **fields}


def test_cards_that_agree_have_no_mismatches_even_with_tags_and_requirements_in_another_order():
    requirements = [{"type": "tag", "tag": "plant", "min": 1}, {"type": "tag", "tag": "animal", "min": 1}]
    our_card = ours(tags=["plant", "animal"], requirements=requirements)
    their_card = theirs(tags=["animal", "plant"], requirements=requirements[::-1])

    assert compare([our_card], [their_card]).mismatches == []


def test_the_open_source_game_leaves_the_event_tag_out_and_the_comparison_adds_it_back():
    comparison = compare(
        [ours(type="event", tags=["event", "space"])], [theirs(type="event", tags=["space"])]
    )

    assert comparison.mismatches == []


def test_every_differing_field_is_a_mismatch():
    comparison = compare(
        [
            ours(
                corporate_era=True,
                cost=12,
                tags=["power"],
                victory_points=1,
                requirements=[{"type": "oxygen", "min": 5}],
            )
        ],
        [theirs(cost=11, tags=["power", "building"], victory_points=2, requirements=[{"type": "oxygen", "min": 4}])],
    )

    assert [(mismatch.field, mismatch.ours, mismatch.theirs) for mismatch in comparison.mismatches] == [
        ("corporate_era", True, False),
        ("cost", 12, 11),
        ("tags", ["power"], ["building", "power"]),
        ("requirements", [{"type": "oxygen", "min": 5}], [{"type": "oxygen", "min": 4}]),
        ("victory_points", 1, 2),
    ]


def test_a_corporations_starting_megacredits_in_its_effect_data_are_compared():
    corporation = {"number": None, "name": "PhoboLog", "type": "corporation", "cost": None}
    common = {"corporate_era": False, "tags": [], "requirements": [], "victory_points": None}
    their_card = {**corporation, **common, "name": "PHOBOLOG", "starting_megacredits": 23}

    same = {**corporation, **common, "id": "phobolog", "effects": {"resources": {"megacredits": 23}}}
    assert compare([same], [their_card]).mismatches == []

    other = {**corporation, **common, "id": "phobolog", "effects": {"resources": {"megacredits": 30}}}
    (mismatch,) = compare([other], [their_card]).mismatches
    assert (mismatch.field, mismatch.ours, mismatch.theirs) == ("starting_megacredits", 30, 23)


def test_a_corporation_not_implemented_yet_has_no_starting_megacredits_to_compare():
    corporation = {"number": None, "name": "Point Luna", "type": "corporation", "cost": None}
    corporation |= {"corporate_era": False, "expansion": "prelude", "tags": [], "requirements": []}
    corporation |= {"victory_points": None}

    comparison = compare([corporation], [{**corporation, "name": "POINT_LUNA", "starting_megacredits": 38}])

    assert comparison.mismatches == []
    assert comparison.not_compared == [
        "Point Luna: not implemented yet, so its starting MegaCredits have no effect data"
    ]


def test_corporations_are_paired_by_name_and_project_cards_by_number():
    corporation = {
        "number": None,
        "type": "corporation",
        "corporate_era": False,
        "cost": None,
        "requirements": [],
        "victory_points": None,
    }
    comparison = compare(
        [
            ours(number=1, name="Underground City", tags=["city"]),
            {**corporation, "id": "phobolog", "name": "PhoboLog", "tags": ["space"]},
        ],
        [
            {**corporation, "name": "PHOBOLOG", "tags": ["space", "space"]},
            theirs(number=1, name="UNDERGROUND_CITY", tags=["city"]),
        ],
    )

    assert [(mismatch.card, mismatch.field) for mismatch in comparison.mismatches] == [("PhoboLog", "tags")]
    assert comparison.names_that_differ == []


PRELUDE_CARD = """
export class AlliedBanks extends PreludeCard {
  constructor() {
    super({
      name: CardName.ALLIED_BANK,
      tags: [Tag.EARTH],
      behavior: {production: {megacredits: 4}, stock: {megacredits: 3}},
      metadata: {
        cardNumber: 'P01',
        description: 'Increase your M€ production 4 steps. Gain 3 M€.',
      },
    });
  }
}
"""


def test_a_prelude_card_definition_has_no_type_or_cost_of_its_own_and_a_number_with_a_p():
    assert parse_open_source_card(PRELUDE_CARD, "AlliedBanks.ts") == {
        "number": "P01",
        "name": "ALLIED_BANK",
        "type": "prelude",
        "cost": None,
        "tags": ["earth"],
        "requirements": [],
        "victory_points": None,
    }


def test_a_prelude_project_card_definition_has_its_type_and_a_number_with_a_p():
    source = project_card("type: CardType.ACTIVE, tags: [Tag.MICROBE], cost: 2,", number="P39", name="PSYCHROPHILES")

    card = parse_open_source_card(source, "Psychrophiles.ts")

    assert (card["number"], card["type"], card["cost"]) == ("P39", "active", 2)


def test_the_prelude_boxs_cards_are_paired_by_their_own_numbers_not_with_the_base_boxs():
    allied_banks = ours(number=1, name="Allied Banks", type="prelude", expansion="prelude", cost=None)
    house_printing = ours(number=36, name="House Printing", expansion="prelude", cost=10)

    comparison = compare(
        [ours(number=1, name="Mine", cost=4), ours(number=36, name="Trees", cost=13), allied_banks, house_printing],
        [
            theirs(number=1, name="MINE", cost=4),
            theirs(number=36, name="TREES", cost=13),
            theirs(number="P01", name="ALLIED_BANKS", type="prelude", cost=None),
            theirs(number="P36", name="HOUSE_PRINTING", cost=11),
        ],
    )

    assert [(each.card, each.field, each.ours, each.theirs) for each in comparison.mismatches] == [
        ("#P36 House Printing", "cost", 10, 11)
    ]
    assert comparison.missing == []


def test_the_box_a_card_comes_in_is_compared():
    comparison = compare([ours(number=1, expansion="prelude")], [theirs(number="P01", expansion="base")])

    assert [(each.field, each.ours, each.theirs) for each in comparison.mismatches] == [
        ("expansion", "prelude", "base")
    ]


def test_a_settled_name_is_listed_apart_from_those_still_open():
    comparison = compare(
        [
            ours(number=11, name="Excentric Sponsor", type="prelude", expansion="prelude", cost=None),
            ours(number=12, name="Experimental Forrest", type="prelude", expansion="prelude", cost=None),
        ],
        [
            theirs(number="P11", name="ECCENTRIC_SPONSOR", type="prelude", cost=None),
            theirs(number="P12", name="EXPERIMENTAL_FOREST", type="prelude", cost=None),
        ],
    )

    assert comparison.names_settled == [("#P11 Excentric Sponsor", "ECCENTRIC_SPONSOR")]
    assert comparison.names_that_differ == [("#P12 Experimental Forrest", "EXPERIMENTAL_FOREST")]
    text = report(comparison, commit="abc")
    assert "## Names settled in the rules notes (1)" in text
    assert "- #P11 Excentric Sponsor: `ECCENTRIC_SPONSOR`" in text
    assert "## Names that differ (1)" in text


def test_cards_missing_from_the_open_source_game_names_that_differ_and_special_points_are_listed():
    comparison = compare(
        [ours(number=1, name="Search for Life"), ours(number=2, name="Martian Rails"), ours(number=3)],
        [theirs(number=1, name="SEARCH_FOR_LIFE", victory_points="special"), theirs(number=2, name="MARTIAN_RAILWAYS")],
    )

    assert comparison.mismatches == []
    assert comparison.not_compared == [
        "#001 Search for Life: the open-source game works out its Victory Points in code"
    ]
    assert comparison.names_that_differ == [("#002 Martian Rails", "MARTIAN_RAILWAYS")]
    assert comparison.missing == ["#003 Test Card"]


def test_the_report_lists_each_mismatch_in_a_table():
    comparison = compare([ours(number=17, name="Noctis City", cost=18)], [theirs(number=17, cost=19)])

    text = report(comparison, commit="4d30aa07f14eeb5aa5647775ce5a7c9e49f6ac04")

    assert "| #017 Noctis City | cost | 18 | 19 |" in text
    assert "4d30aa07f14eeb5aa5647775ce5a7c9e49f6ac04" in text


def test_the_saved_report_has_no_open_entries():
    saved = REPORT.read_text(encoding="utf-8")

    assert "## Differences (0)" in saved
    assert "## Names that differ (0)" in saved
    assert "## Missing from the open-source game (0)" in saved


def test_the_saved_report_is_up_to_date_with_the_card_file():
    if not (CACHE / COMMIT).exists():
        pytest.skip("the open-source game's card definitions are not saved here")

    comparison = compare(tm_engine.card_catalog(), load_open_source_cards(COMMIT))

    assert report(comparison, commit=COMMIT) == REPORT.read_text(encoding="utf-8")
