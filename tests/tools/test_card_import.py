"""The card import (`uv run python -m tools.card_import`) turns the fan-made card list's
HTML into our card file (ADR 0005). These tests feed it cards copied from that page."""

import json
import re

import pytest
import tm_engine

from tools.card_import import (
    CARD_FILE,
    ICONS,
    PAGE,
    PRINTED_FIELDS,
    PROJECT,
    STYLESHEET,
    card_file_text,
    check_card_set,
    icons_used,
    keep_written_by_hand,
    parse_card_list,
)


def card_list_with(content: str, *, description: str = "(As printed.)", name: str = "Test Card") -> str:
    """The card list page with one Automated base-game card, whose middle part holds `content`."""
    return f"""
    <ul class="myUL" id="projectCards">
      <li onclick="getClickedCard();" class="filterDiv automated standard">
        <div class="title background-color-automated">{name}</div>
        <div class="price">10</div>
        <div class="number">#100</div>
        <div class="content">
          {content}
          <div class="description">{description}</div>
        </div>
      </li>
    </ul>
    """


def the_card(html: str) -> dict:
    [card] = parse_card_list(html)
    return card

DEEP_WELL_HEATING = """
<ul class="myUL" id="projectCards">
  <!--3-->
  <li
    onclick="getClickedCard();"
    class="filterDiv automated buildingTag powerTag standard"
  >
    <div class="title background-color-automated">
      Deep Well Heating
    </div>
    <div class="price">13</div>
    <div class="tag tag1 tag-building"></div>
    <div class="tag tag2 tag-power"></div>
    <div class="number">#003</div>
    <div class="content">
      <div class="production-box">
        <div class="energy production"></div>
      </div>
      <div
        class="tile temperature-tile"
        style="margin-left: 20px"
      ></div>
      <div class="description">
        (Increase your Energy production 1 step. Increase temperature 1
        step.)
      </div>
    </div>
  </li>
</ul>
"""


def test_a_project_card_keeps_its_printed_data_and_its_face():
    assert parse_card_list(DEEP_WELL_HEATING) == [
        {
            "id": "deep_well_heating",
            "number": 3,
            "name": "Deep Well Heating",
            "type": "automated",
            "corporate_era": False,
            "expansion": "base",
            "cost": 13,
            "tags": ["building", "power"],
            "requirements": [],
            "victory_points": None,
            "text": "(Increase your Energy production 1 step. Increase temperature 1 step.)",
            # Whitespace is collapsed as a browser collapses it, and left where it is.
            "face": {
                "content": {
                    "tag": "div",
                    "class": "content",
                    "children": [
                        " ",
                        {
                            "tag": "div",
                            "class": "production-box",
                            "children": [" ", {"tag": "div", "class": "energy production"}, " "],
                        },
                        " ",
                        {"tag": "div", "class": "tile temperature-tile", "style": {"margin-left": "20px"}},
                        " ",
                        {
                            "tag": "div",
                            "class": "description",
                            "children": [" (Increase your Energy production 1 step. Increase temperature 1 step.) "],
                        },
                        " ",
                    ],
                }
            },
        }
    ]


def test_a_title_or_middle_part_with_a_style_of_its_own_keeps_it():
    page = """
    <ul class="myUL">
      <li class="filterDiv events eventTag corporate">
        <div class="title background-color-events" style="font-size: 14px">CEO's Favorite Project</div>
        <div class="price">1</div>
        <div class="tag tag1 tag-event"></div>
        <div class="number">#149</div>
        <div class="corporate-icon project-icon"></div>
        <div class="content" style="font-size: 14px; font-weight: normal">
          ADD 1 RESOURCE TO A CARD WITH AT LEAST 1 RESOURCE ON IT
        </div>
      </li>
    </ul>
    """

    face = the_card(page)["face"]

    assert face["title_style"] == {"font-size": "14px"}
    assert face["content"]["style"] == {"font-size": "14px", "font-weight": "normal"}


def test_a_card_without_a_description_has_the_text_of_its_middle_part():
    card = the_card(
        card_list_with(
            '<div class="points points-big">4</div>'
            "<div>ACTION: LOOK AT THE TOP CARD AND EITHER BUY IT<br />OR DISCARD IT</div>",
            description="",
        ).replace('<div class="description"></div>', "")
    )

    assert card["text"] == "ACTION: LOOK AT THE TOP CARD AND EITHER BUY IT OR DISCARD IT"


def test_a_space_at_the_end_of_an_inline_element_stays_inside_it():
    card = the_card(
        card_list_with('<span style="font-size: 14px">NEXT CARD: </span>\n <div class="resource money">-8</div>')
    )

    span = {"tag": "span", "style": {"font-size": "14px"}, "children": ["NEXT CARD: "]}
    assert span in card["face"]["content"]["children"]


@pytest.mark.parametrize(
    ("printed", "description", "requirements"),
    [
        ('<div class="requirements">2% O2</div>', "", [{"type": "oxygen", "min": 2}]),
        ('<div class="requirements requirements-max">max 5% O2</div>', "", [{"type": "oxygen", "max": 5}]),
        ('<div class="requirements">-24 C</div>', "", [{"type": "temperature", "min": -24}]),
        ('<div class="requirements">0 C</div>', "", [{"type": "temperature", "min": 0}]),
        ('<div class="requirements">+4 C</div>', "", [{"type": "temperature", "min": 4}]),
        ('<div class="requirements requirements-max">max -12 C</div>', "", [{"type": "temperature", "max": -12}]),
        ('<div class="requirements">3 Oceans</div>', "", [{"type": "oceans", "min": 3}]),
        ('<div class="requirements requirements-max">max 3 Oceans</div>', "", [{"type": "oceans", "max": 3}]),
        ('<div class="requirements">5 Science</div>', "", [{"type": "tag", "tag": "science", "min": 5}]),
        ('<div class="requirements">2 Power</div>', "", [{"type": "tag", "tag": "power", "min": 2}]),
        ('<div class="requirements">Jovian</div>', "", [{"type": "tag", "tag": "jovian", "min": 1}]),
        (
            '<div class="requirements">Plant Microbe Animal</div>',
            "(Requires a Plant tag, a Microbe tag, and an Animal tag.)",
            [
                {"type": "tag", "tag": "plant", "min": 1},
                {"type": "tag", "tag": "microbe", "min": 1},
                {"type": "tag", "tag": "animal", "min": 1},
            ],
        ),
        ('<div class="requirements">Earth Earth</div>', "", [{"type": "tag", "tag": "earth", "min": 2}]),
        (
            '<div class="requirements">Titanium production</div>',
            "",
            [{"type": "production", "resource": "titanium", "min": 1}],
        ),
        (
            '<div class="requirements">Forest</div>',
            "(Requires that you have a greenery tile.)",
            [{"type": "tiles", "tile": "greenery", "owner": "you", "min": 1}],
        ),
        (
            '<div class="requirements">2 Cities</div>',
            "(Requires two cities in play.)",
            [{"type": "tiles", "tile": "city", "owner": "anyone", "min": 2}],
        ),
    ],
)
def test_requirements_are_read_from_the_printed_requirement(printed, description, requirements):
    assert the_card(card_list_with(printed, description=description))["requirements"] == requirements


def test_a_requirement_the_import_does_not_know_stops_it_and_names_the_card():
    with pytest.raises(ValueError, match="Test Card.*'3 Moons'"):
        parse_card_list(card_list_with('<div class="requirements">3 Moons</div>'))


@pytest.mark.parametrize(
    ("printed", "description", "victory_points"),
    [
        ('<div class="points points-big">2</div>', "", 2),
        ('<div class="points points-big">-1</div>', "", -1),
        (
            '<div class="points points-big">1/<span class="tag-jovian resource-tag"></span></div>',
            "(1 VP for each Jovian tag you have.)",
            {"points": 1, "per": 1, "of": {"tag": "jovian"}},
        ),
        (
            '<div class="points">1/ <div class="animal resource"></div></div>',
            "(1 VP per Animal on this card.)",
            {"points": 1, "per": 1, "of": {"card_resource": "animal"}},
        ),
        (
            '<div class="points">1/2 <div class="resource microbe"></div></div>',
            "(1 VP per 2 Microbes on this card.)",
            {"points": 1, "per": 2, "of": {"card_resource": "microbe"}},
        ),
        (
            '<div class="points points-big"><span style="margin-left: -8px">2/</span>'
            '<div class="science resource"></div></div>',
            "(2 VP for each science resource on this card.)",
            {"points": 2, "per": 1, "of": {"card_resource": "science"}},
        ),
        (
            '<div class="points points-big"><span style="margin-right: -8px">3/</span>'
            '<span class="resource science"></span></div>',
            "(3 VPs if you have one or more Science resources here.)",
            {"points": 3, "at_least": 1, "of": {"card_resource": "science"}},
        ),
        (
            '<div class="points">1/<span class="resource ocean-resource"></span></div>',
            "1 ADDITIONAL VP FOR EACH <br />OCEAN TILE ADJACENT <br /> TO THIS CITY TILE.",
            {"points": 1, "per": 1, "of": {"adjacent": "ocean"}},
        ),
        (
            '<div class="points big">1/ <div class="tile city-tile-small"></div></div>',
            "(Place this tile. 1 VP PER<br /> ADJACENT CITY TILE.)",
            {"points": 1, "per": 1, "of": {"adjacent": "city"}},
        ),
        (
            '<div class="points big" style="font-size: 24px">1/3 '
            '<div class="tile city-tile-small red-outline"></div></div>',
            "(Increase your MC production 5 steps. 1 VP for every 3rd City in play.)",
            {"points": 1, "per": 3, "of": {"tiles_in_play": "city"}},
        ),
    ],
)
def test_victory_points_are_read_from_the_printed_points(printed, description, victory_points):
    assert the_card(card_list_with(printed, description=description))["victory_points"] == victory_points


def test_victory_points_the_import_does_not_know_stop_it_and_name_the_card():
    with pytest.raises(ValueError, match="Test Card.*Victory Points"):
        parse_card_list(card_list_with('<div class="points">1/ <div class="resource floater"></div></div>'))


def test_the_text_keeps_paragraphs_apart_and_joins_lines_broken_for_the_layout():
    card = the_card(
        card_list_with(
            '<div class="description">(Action: Spend 1 MC to reveal the top card.)<br />\n  <br />'
            "(3 VPs if you have one or more Science resources here.)</div>",
            description="(Place this tile. 1 VP PER<br />\n ADJACENT CITY TILE.)",
        )
    )

    assert card["text"] == (
        "(Action: Spend 1 MC to reveal the top card.)\n"
        "(3 VPs if you have one or more Science resources here.)\n"
        "(Place this tile. 1 VP PER ADJACENT CITY TILE.)"
    )


def test_a_description_inside_a_description_is_part_of_the_text():
    # As on Valley Trust, whose starting MegaCredits are drawn beside its text.
    card = the_card(
        card_list_with(
            "",
            description='<div class="resource money">37</div><div class="description">(You start with 37 MC.)</div>',
        )
    )

    assert card["text"] == "(You start with 37 MC.)"


def test_a_word_drawn_as_an_icon_is_left_out_of_the_text():
    # As on Vitor, whose first action is drawn as an orange label reading AWARDS.
    card = the_card(
        card_list_with("", description='<span style="background: orange">AWARDS</span><br />(Fund an award for free.)')
    )

    assert card["text"] == "(Fund an award for free.)"


def test_numbers_drawn_as_icons_are_left_out_of_the_text():
    card = the_card(card_list_with("", description='<div class="resource money">57</div><br />(You start with 57 MC.)'))

    assert card["text"] == "(You start with 57 MC.)"


def corporation(number: int, logo: str, *, card_set: str = "standard", tags: str = "") -> str:
    """A Corporation as the card list draws it: an effect box, a logo made of styled text and
    the starting Resources."""
    return f"""
      <li id="#CORP{number:02}" onclick="getClickedCard();" class="filterDiv corporation {card_set}">
        {tags}
        <div class="corporationLabel">CORPORATION</div>
        <div class="contentCorporation">
          <div class="corporationEffectBox">
            <div class="corporationEffectBoxLabel">EFFECT</div>
            <div class="resource money">20</div>
            <div class="description" style="text-align: center; margin-top: 0px">
              (Effect: After you pay for a card or standard project with a
              basic cost of 20MC or more, you gain 4MC.)
            </div>
          </div>
          <span style="font-size: 40px; color: white;">{logo}</span><br /><br />
          <div class="description" style="text-align: center">
            <div class="resource money" style="margin-top: -10px">57</div>
            <br />
            (You start with 57 MC.)
          </div>
        </div>
      </li>
    """


def test_a_corporation_is_named_after_its_logo_and_has_no_cost_or_number():
    [credicor] = parse_card_list(f'<ul class="myUL">{corporation(1, "credicor")}</ul>')

    assert {key: value for key, value in credicor.items() if key != "face"} == {
        "id": "credicor",
        "number": None,
        "name": "CrediCor",
        "type": "corporation",
        "corporate_era": False,
        "expansion": "base",
        "cost": None,
        "tags": [],
        "requirements": [],
        "victory_points": None,
        "text": "(Effect: After you pay for a card or standard project with a basic cost of 20MC or more, "
        "you gain 4MC.)\n(You start with 57 MC.)",
    }
    content = credicor["face"]["content"]
    assert content["class"] == "contentCorporation"
    logo = {"tag": "span", "style": {"font-size": "40px", "color": "white"}, "children": ["credicor"]}
    assert logo in content["children"]


def test_corporate_era_corporations_and_corporation_tags_are_marked():
    tags = '<div class="tag tag1 tag-building"></div><div class="tag tag2 tag-building"></div>'
    mining_guild = corporation(4, "MINING<br />GUILD", tags=tags)
    saturn_systems = corporation(12, "SATURN &#x25CF; SYSTEMS", card_set="corporate")
    page = f'<ul class="myUL">{mining_guild}{saturn_systems}</ul>'

    [mining_guild, saturn_systems] = parse_card_list(page)

    assert (mining_guild["name"], mining_guild["tags"], mining_guild["corporate_era"]) == (
        "Mining Guild",
        ["building", "building"],
        False,
    )
    assert (saturn_systems["id"], saturn_systems["corporate_era"]) == ("saturn_systems", True)


def test_a_corporation_whose_logo_does_not_match_its_name_stops_the_import():
    with pytest.raises(ValueError, match="CORP03.*Helion.*phobolog"):
        parse_card_list(f'<ul class="myUL">{corporation(3, "phobolog")}</ul>')


def test_promo_and_other_expansions_cards_are_left_out():
    page = f"""
    <ul class="myUL">
      <li class="filterDiv automated promo">
        <div class="title background-color-automated">Advertising</div>
        <div class="price">4</div><div class="number">#X14</div><div class="content"></div>
      </li>
      <li class="filterDiv prelude prelude-card noneTag promo">
        <div class="title background-color-prelude">Merger</div>
        <div class="number">#X41</div><div class="content"></div>
      </li>
      {corporation(13, "aphrodite", card_set="venusNext")}
      {corporation(41, "applied science", card_set="prelude2")}
    </ul>
    """

    assert parse_card_list(page) == []


DONATION = """
<li class="filterDiv prelude prelude-card noneTag">
  <div class="title background-color-prelude">Donation</div>
  <div class="prelude-label">PRELUDE</div>
  <div class="number" style="margin-left: 99px">#P08</div>
  <div class="prelude-icon preludeCard-icon"></div>
  <div class="content">
    <div class="resource money">21</div>
    <div class="description">(Gain 21 MC.)</div>
  </div>
</li>
"""

HOUSE_PRINTING = """
<li class="filterDiv automated buildingTag prelude">
  <div class="title background-color-automated">House Printing</div>
  <div class="price">10</div>
  <div class="tag tag1 tag-building"></div>
  <div class="number">#P36</div>
  <div class="prelude-icon project-icon"></div>
  <div class="content">
    <div class="points points-big">1</div>
    <div class="description">(Increase your steel production 1 step.)</div>
  </div>
</li>
"""


def test_a_prelude_card_has_its_own_type_a_number_of_its_own_and_no_cost():
    [donation] = parse_card_list(f'<ul class="myUL">{DONATION}</ul>')

    assert {key: value for key, value in donation.items() if key != "face"} == {
        "id": "donation",
        "number": 8,
        "name": "Donation",
        "type": "prelude",
        "corporate_era": False,
        "expansion": "prelude",
        "cost": None,
        "tags": [],
        "requirements": [],
        "victory_points": None,
        "text": "(Gain 21 MC.)",
    }


def test_a_prelude_card_that_ignores_requirements_has_none_of_its_own():
    ecology_experts = DONATION.replace(
        '<div class="resource money">21</div>',
        '<div class="requirements"><div>X</div><div>Project Requirements</div></div>',
    )

    assert parse_card_list(f'<ul class="myUL">{ecology_experts}</ul>')[0]["requirements"] == []


def test_preludes_project_cards_are_marked_as_prelude_and_keep_their_own_type():
    [house_printing] = parse_card_list(f'<ul class="myUL">{HOUSE_PRINTING}</ul>')

    assert (house_printing["type"], house_printing["expansion"]) == ("automated", "prelude")
    assert (house_printing["number"], house_printing["cost"], house_printing["victory_points"]) == (36, 10, 1)


@pytest.mark.parametrize(
    ("page_id", "logo", "card_id", "name"),
    [
        (18, "Cheung Shing MARS", "cheung_shing_mars", "Cheung Shing Mars"),
        (19, "POINT LUNA", "point_luna", "Point Luna"),
        (20, "ROBINSON INDUSTRIES", "robinson_industries", "Robinson Industries"),
        (21, "VALLEY TRUST", "valley_trust", "Valley Trust"),
        (22, "VIT O R", "vitor", "Vitor"),
    ],
)
def test_preludes_corporations_are_named_after_their_logos(page_id, logo, card_id, name):
    [found] = parse_card_list(f'<ul class="myUL">{corporation(page_id, logo, card_set="prelude")}</ul>')

    assert (found["id"], found["name"], found["type"], found["expansion"]) == (card_id, name, "corporation", "prelude")


def test_new_cards_come_after_the_base_box_so_no_card_of_a_game_without_prelude_moves():
    page = f"""
    <ul class="myUL">
      {DONATION}
      {corporation(19, "POINT LUNA", card_set="prelude")}
      {corporation(1, "credicor")}
      {HOUSE_PRINTING}
      <li class="filterDiv automated standard">
        <div class="title background-color-automated">Test Card</div>
        <div class="price">10</div><div class="number">#100</div><div class="content"></div>
      </li>
    </ul>
    """

    assert [card["id"] for card in parse_card_list(page)] == [
        "test_card",
        "credicor",
        "house_printing",
        "point_luna",
        "donation",
    ]


def test_a_saved_page_without_all_the_cards_stops_the_import():
    cards = parse_card_list(PAGE.read_text(encoding="utf-8"))

    check_card_set(cards)
    with pytest.raises(ValueError, match="46 cards of Prelude"):
        check_card_set(cards[:-1])
    with pytest.raises(ValueError, match="#001"):
        check_card_set(cards[1:])


def test_importing_again_updates_the_printed_data_and_keeps_what_was_written_by_hand():
    [imported] = parse_card_list(DEEP_WELL_HEATING)
    written_by_hand = {"effects": [{"production": {"energy": 1}}, {"raise": "temperature"}]}
    earlier = {**imported, "cost": 12, **written_by_hand}

    [card] = keep_written_by_hand([imported], earlier=[earlier])

    assert card == {**imported, **written_by_hand}
    assert list(card)[-1] == "effects"


def test_a_card_with_data_written_by_hand_must_still_be_on_the_card_list():
    [imported] = parse_card_list(DEEP_WELL_HEATING)
    gone = {**imported, "id": "deep_well_heater", "effects": []}

    with pytest.raises(ValueError, match="deep_well_heater"):
        keep_written_by_hand([imported], earlier=[gone])


def test_the_card_file_holds_the_cards_as_json():
    cards = parse_card_list(DEEP_WELL_HEATING)

    assert json.loads(card_file_text(cards))["cards"] == cards


def test_only_the_icons_that_the_catalogs_cards_use_are_fetched():
    stylesheet = """
    @font-face { font-family: Prototype; src: url(../fonts/Prototype.ttf); }
    .price { background-image: url(../images/megacredits/megacredit.png); }
    .tag-building { background-image: url("../images/tags/building.png"); }
    .tag-venus { background-image: url("../images/tags/venus.png"); }
    li.automated::before { background-image: url(../images/mars.png); }
    li.prelude-card::before { background-image: url(../images/mars.png); }
    /* .energy { background-image: url(../images/resources/power.png); } */
    .production-box .energy { background-image: url(../images/resources/power.png); }
    """

    assert icons_used(DEEP_WELL_HEATING, stylesheet) == [
        "fonts/Prototype.ttf",
        "images/mars.png",
        "images/megacredits/megacredit.png",
        "images/resources/power.png",
        "images/tags/building.png",
    ]


def test_every_icon_the_cards_use_is_stored_in_the_project():
    # The GUI must never need the card list's website, so every image and font the catalog's
    # cards use, and every one the GUI's card stylesheet refers to, is in gui/public/card-list/.
    needed = icons_used(PAGE.read_text(encoding="utf-8"), STYLESHEET.read_text(encoding="utf-8"))
    stylesheet = (PROJECT / "gui" / "src" / "cards" / "cardList.css").read_text(encoding="utf-8")
    referred_to = re.findall(r'url\("/card-list/([^"]+)"\)', stylesheet)

    assert len(needed) == 41
    assert sorted(set(referred_to)) == needed
    assert [path for path in needed if not (ICONS / path).is_file()] == []


@pytest.mark.parametrize(
    ("written", "card_id", "name"),
    [
        ("Anti-gravity Technology", "anti_gravity_technology", "Anti-Gravity Technology"),
        ("Metal-rich Asteroid", "metal_rich_asteroid", "Metal-Rich Asteroid"),
        ("PSYCHROPHILES", "psychrophiles", "Psychrophiles"),
        ("RESEARCH COORDINATION", "research_coordination", "Research Coordination"),
        ("SF MEMORIAL", "sf_memorial", "SF Memorial"),
    ],
)
def test_names_the_card_list_writes_with_odd_capitals_are_corrected(written, card_id, name):
    card = the_card(card_list_with("", name=written))

    assert (card["id"], card["name"]) == (card_id, name)


def test_the_card_file_is_what_importing_again_would_write():
    # So running the import changes nothing.
    written = CARD_FILE.read_text(encoding="utf-8")
    imported = parse_card_list(PAGE.read_text(encoding="utf-8"))

    assert card_file_text(keep_written_by_hand(imported, earlier=json.loads(written)["cards"])) == written


def test_the_engine_holds_what_the_import_makes_of_the_saved_card_list():
    # The committed card file must be up to date with the import, and the engine's card
    # catalog must give back every printed field unchanged.
    imported = parse_card_list(PAGE.read_text(encoding="utf-8"))

    assert [{field: card[field] for field in PRINTED_FIELDS} for card in tm_engine.card_catalog()] == imported
