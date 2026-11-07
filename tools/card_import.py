"""Imports the printed card data from the fan-made card list (ADR 0005) into our card file:

    uv run python -m tools.card_import              # from the saved copy of the page
    uv run python -m tools.card_import --download   # fetch the page and the icons again first

The card list's HTML is parsed into one entry per card of the catalog: the base box's 208
Project Cards and 12 Corporations (ADR 0003), then Prelude's 7 Project Cards, 5 Corporations
and 35 Prelude Cards (ADR 0011). Promo cards and other expansions on the page are left out.
Each entry holds the card's printed data (name, number, type, expansion, cost, Tags,
Requirements, Victory Points and text) and its face: the card's middle part as a tree of
elements, which the GUI draws with the card list's stylesheet.

The page and its stylesheet are kept in `tools/card_list_snapshot/`, so the import runs
without the website and a diff shows what changed there. `--download` refreshes them and
fetches the icons the cards use into `gui/public/card-list/`. The card file,
`engine/cards/cards.json`, is committed; the engine builds it in, so nothing depends on the
website at runtime.
"""

import argparse
import json
import re
import urllib.request
from collections import Counter
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

PROJECT = Path(__file__).resolve().parent.parent
SNAPSHOT = PROJECT / "tools" / "card_list_snapshot"
PAGE = SNAPSHOT / "cards-list.html"
STYLESHEET = SNAPSHOT / "mystyles.css"
CARD_FILE = PROJECT / "engine" / "cards" / "cards.json"
ICONS = PROJECT / "gui" / "public" / "card-list"

SITE = "https://ssimeonoff.github.io/"
PAGE_URL = SITE + "cards-list"
STYLESHEET_URL = SITE + "css/mystyles.css"

# How many cards the catalog has of each kind: in the base box (ADR 0003), and in Prelude (ADR
# 0011). Prelude numbers its cards on from its Prelude Cards, #P01 to #P35, to its Project Cards,
# #P36 to #P42.
PROJECT_CARDS = 208
CORPORATIONS = 12
PRELUDE_CARDS = 35
PRELUDE_PROJECT_CARDS = 7
PRELUDE_CORPORATIONS = 5

# The fields the import writes. Any other field of a card in the card file was written by
# hand (ticket 08 onwards: effect data, ADR 0009) and is kept when the import runs again.
PRINTED_FIELDS = (
    "id",
    "number",
    "name",
    "type",
    "corporate_era",
    "expansion",
    "cost",
    "tags",
    "requirements",
    "victory_points",
    "text",
    "face",
)

ABOUT_THE_CARD_FILE = (
    "The card catalog (ADR 0005). tools/card_import.py writes each card's printed fields "
    f"({', '.join(PRINTED_FIELDS)}) from the fan-made card list at ssimeonoff.github.io/cards-list, "
    "and rewrites them when run again. Any other field is written by hand and kept."
)

# The page's own name for each card type.
CARD_TYPES = {
    "automated": "automated",
    "active": "active",
    "events": "event",
    "corporation": "corporation",
    "prelude-card": "prelude",
}

# The page's own name for the sets in the catalog: the base game, Corporate Era and Prelude. The
# page marks the promo Prelude Cards (Corporate Archives, Merger and so on) as both Prelude and
# promo; they, and everything else on the page (Venus Next, Prelude 2, Colonies, Turmoil), are
# left out.
BASE_GAME, CORPORATE_ERA, PRELUDE, PROMO = "standard", "corporate", "prelude", "promo"

# Corporations have no title on the card list, only a logo drawn with styled text, so their
# names come from here, by the page's own id for each. The import checks each logo against
# its name.
CORPORATION_NAMES = {
    "#CORP01": "CrediCor",
    "#CORP02": "EcoLine",
    "#CORP03": "Helion",
    "#CORP04": "Mining Guild",
    "#CORP05": "Interplanetary Cinematics",
    "#CORP06": "Inventrix",
    "#CORP07": "PhoboLog",
    "#CORP08": "Tharsis Republic",
    "#CORP09": "Thorgate",
    "#CORP10": "United Nations Mars Initiative",
    "#CORP11": "Teractor",
    "#CORP12": "Saturn Systems",
    "#CORP18": "Cheung Shing Mars",
    "#CORP19": "Point Luna",
    "#CORP20": "Robinson Industries",
    "#CORP21": "Valley Trust",
    "#CORP22": "Vitor",
}

# Names the card list writes with odd capitals. Printed cards show titles in capitals, so
# the card file uses title case throughout (decided with the user, 2026-10-23).
NAME_CORRECTIONS = {
    "Underground city": "Underground City",
    "Anti-gravity Technology": "Anti-Gravity Technology",
    "Metal-rich Asteroid": "Metal-Rich Asteroid",
    "PSYCHROPHILES": "Psychrophiles",
    "RESEARCH COORDINATION": "Research Coordination",
    "SF MEMORIAL": "SF Memorial",
    # As printed, which the user checked (see docs/rules-notes.md, "The names of Prelude's cards").
    "Biolab": "Biolabs",
}

# The Tags printed on cards, as the card file names them.
TAGS = (
    "building",
    "space",
    "power",
    "science",
    "jovian",
    "earth",
    "plant",
    "microbe",
    "animal",
    "city",
    "event",
    "wild",
)

# The Card Resources Victory Points can count, as the card file names them.
CARD_RESOURCES = ("animal", "microbe", "science", "fighter")

# Elements that never have content, so they are never closed.
VOID_ELEMENTS = {"br", "img", "hr", "input", "meta", "link"}

# The whitespace HTML collapses. A no-break space (&nbsp;) is not part of it.
HTML_WHITESPACE = re.compile(r"[ \t\n\r\f]+")


@dataclass
class Element:
    tag: str
    classes: list[str]
    style: dict[str, str]
    id: str = ""
    children: list["Element | str"] = field(default_factory=list)

    def has_class(self, name: str) -> bool:
        return name in self.classes

    def elements(self) -> list["Element"]:
        """The child elements, without the text between them."""
        return [child for child in self.children if isinstance(child, Element)]

    def descendants(self) -> list["Element"]:
        """Every element inside this one, at any depth, in the order they appear."""
        return [found for element in self.elements() for found in [element, *element.descendants()]]

    def outermost(self, class_name: str) -> list["Element"]:
        """The elements inside this one with the class `class_name`, at any depth, except
        those inside another such element."""
        found = []
        for element in self.elements():
            found.extend([element] if element.has_class(class_name) else element.outermost(class_name))
        return found

    def text(self) -> str:
        """All the text inside, with whitespace collapsed as a browser shows it."""
        words = "".join(child if isinstance(child, str) else child.text() for child in self.children)
        return HTML_WHITESPACE.sub(" ", words).strip()


class _TreeBuilder(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Element("root", [], {})
        self.open: list[Element] = [self.root]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        classes = (attributes.get("class") or "").split()
        element = Element(tag, classes, parse_style(attributes.get("style") or ""), attributes.get("id") or "")
        self.open[-1].children.append(element)
        if tag not in VOID_ELEMENTS:
            self.open.append(element)

    def handle_endtag(self, tag: str) -> None:
        # Close up to the matching element; a stray end tag closes nothing.
        for depth in range(len(self.open) - 1, 0, -1):
            if self.open[depth].tag == tag:
                del self.open[depth:]
                return

    def handle_data(self, data: str) -> None:
        self.open[-1].children.append(data)


def parse_html(html: str) -> Element:
    builder = _TreeBuilder()
    builder.feed(html)
    builder.close()
    return builder.root


def parse_style(style: str) -> dict[str, str]:
    """An inline style as {property: value}, e.g. {"margin-left": "20px"}."""
    declarations = {}
    for declaration in _without_comments(style).split(";"):
        name, colon, value = declaration.partition(":")
        if colon:
            declarations[name.strip().lower()] = HTML_WHITESPACE.sub(" ", value).strip()
    return declarations


def _without_comments(css: str) -> str:
    return re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)


def parse_card_list(html: str) -> list[dict[str, Any]]:
    """The printed data of every catalog card on the card list page, in the catalog's order: the
    base box's Project Cards and Corporations, then Prelude's Project Cards, Corporations and
    Prelude Cards. A Game names cards by their place in it, so new cards only ever go last. Within
    each kind, cards keep the page's order."""
    return sorted((_card(item) for item in _catalog_cards(parse_html(html))), key=_place_in_catalog)


def _place_in_catalog(card: dict[str, Any]) -> tuple[bool, int]:
    kind = {"corporation": 1, "prelude": 2}.get(card["type"], 0)
    return card["expansion"] != "base", kind


def _catalog_cards(page: Element) -> list[Element]:
    """The page's list item for each catalog card: each card on the page is an <li> with the class
    "filterDiv", and classes for its type and its set."""
    return [
        item
        for item in page.outermost("filterDiv")
        if item.tag == "li"
        and any(item.has_class(name) for name in CARD_TYPES)
        and (
            item.has_class(BASE_GAME)
            or item.has_class(CORPORATE_ERA)
            or (item.has_class(PRELUDE) and not item.has_class(PROMO))
        )
    ]


def _expansion(item: Element) -> str:
    """What the box a card comes in is called. Corporate Era is part of the base box."""
    return "prelude" if item.has_class(PRELUDE) else "base"


def _card(item: Element) -> dict[str, Any]:
    card_type = next(CARD_TYPES[name] for name in CARD_TYPES if item.has_class(name))
    if card_type == "corporation":
        return _corporation(item)
    is_a_prelude_card = card_type == "prelude"
    title = _child(item, "title")
    name = NAME_CORRECTIONS.get(title.text(), title.text())
    content = _child(item, "content")
    text = _text(content)
    try:
        # A Prelude Card has no Requirements. What Ecology Experts draws as one is its effect.
        requirements = [] if is_a_prelude_card else _requirements(content, text)
        victory_points = _victory_points(content, text)
    except ValueError as problem:
        raise ValueError(f"{name}: {problem}") from None
    return {
        "id": card_id(name),
        "number": int(_child(item, "number").text().removeprefix("#").removeprefix("P")),
        "name": name,
        "type": card_type,
        "corporate_era": item.has_class(CORPORATE_ERA),
        "expansion": _expansion(item),
        "cost": None if is_a_prelude_card else int(_child(item, "price").text()),
        "tags": _tags(item),
        "requirements": requirements,
        "victory_points": victory_points,
        "text": text,
        "face": _face(content, title),
    }


def _corporation(item: Element) -> dict[str, Any]:
    """A Corporation: no cost, number, Requirements or Victory Points, and a logo for a title."""
    content = _child(item, "contentCorporation")
    name = CORPORATION_NAMES.get(item.id)
    letters = re.sub(r"[^A-Z]", "", content.text().upper())
    if name is None or re.sub(r"[^A-Z]", "", name.upper()) not in letters:
        raise ValueError(
            f"the card list's Corporation {item.id} should be {name}, but it reads {content.text()!r}"
        )
    return {
        "id": card_id(name),
        "number": None,
        "name": name,
        "type": "corporation",
        "corporate_era": item.has_class(CORPORATE_ERA),
        "expansion": _expansion(item),
        "cost": None,
        "tags": _tags(item),
        "requirements": [],
        "victory_points": None,
        "text": _text(content),
        "face": _face(content),
    }


def _child(item: Element, class_name: str) -> Element:
    found = [child for child in item.elements() if child.has_class(class_name)]
    if len(found) != 1:
        raise ValueError(f"expected one {class_name!r} in a card, found {len(found)}")
    return found[0]


def printed_number(card: dict[str, Any]) -> str | None:
    """A card's number as printed, "#056" or Prelude's "#P36". Corporations have none."""
    if card["number"] is None:
        return None
    return f"#P{card['number']:02}" if card["expansion"] == "prelude" else f"#{card['number']:03}"


def card_id(name: str) -> str:
    """How Scenarios, Option details and Replays name a card: "CEO's Favorite Project" is
    "ceos_favorite_project"."""
    return re.sub(r"[^a-z0-9]+", "_", name.lower().replace("'", "")).strip("_")


def _tags(item: Element) -> list[str]:
    """The Tags in the order printed, from the top right corner leftwards."""
    tags = [child for child in item.elements() if child.has_class("tag")]
    tags.sort(key=lambda tag: next(name for name in tag.classes if re.fullmatch(r"tag\d", name)))
    return [_named(tag, "tag-") for tag in tags]


def _requirements(content: Element, text: str) -> list[dict[str, Any]]:
    """The Requirements printed at the top of the card's middle part, such as "max 5% O2"
    (Oxygen at most 5 %), "3 Oceans", "2 Power" (2 power Tags) or "Titanium production"."""
    requirements = []
    for printed in (element for element in content.elements() if element.has_class("requirements")):
        requirements.extend(_requirement(printed, text))
    return requirements


def _requirement(printed: Element, text: str) -> list[dict[str, Any]]:
    wording = printed.text()
    limit = "max" if printed.has_class("requirements-max") else "min"
    if (limit == "max") != wording.startswith("max "):
        raise ValueError(f"the requirement {wording!r} disagrees with its own maximum mark")
    wording = wording.removeprefix("max ")
    global_parameters = {
        "oxygen": r"([+-]?\d+)% O2",
        "temperature": r"([+-]?\d+) C",
        "oceans": r"(\d+) Oceans?",
    }
    for parameter, pattern in global_parameters.items():
        if found := re.fullmatch(pattern, wording):
            return [{"type": parameter, limit: int(found[1])}]
    if limit == "min":
        if found := re.fullmatch(r"(\d+ )?(\w+)", wording):
            if (tag := found[2].lower()) in TAGS:
                return [{"type": "tag", "tag": tag, "min": int(found[1] or 1)}]
        if all(word.lower() in TAGS for word in wording.split()):
            # A Tag drawn twice is two of it: "Earth Earth" on Space Hotels.
            counted = Counter(word.lower() for word in wording.split())
            return [{"type": "tag", "tag": tag, "min": count} for tag, count in counted.items()]
        if found := re.fullmatch(r"(Steel|Titanium) production", wording):
            return [{"type": "production", "resource": found[1].lower(), "min": 1}]
        if wording == "Forest":
            return [{"type": "tiles", "tile": "greenery", "owner": "you", "min": 1}]
        if found := re.fullmatch(r"(\d+) Cities", wording):
            # The icons don't show whose Cities count; the text says "in play" when anyone's do.
            owner = "anyone" if "in play" in text else "you"
            return [{"type": "tiles", "tile": "city", "owner": owner, "min": int(found[1])}]
    raise ValueError(f"unknown requirement {wording!r}")


def _victory_points(content: Element, text: str) -> int | dict[str, Any] | None:
    """The Victory Points in the card's bottom right corner: a number such as "2" or "-1", or
    points for something, such as "1/2" with a microbe icon (1 point per 2 microbes here)."""
    printed = [element for element in content.elements() if element.has_class("points")]
    if not printed:
        return None
    [points] = printed
    wording = points.text()  # icons have no text of their own
    icon = next((element for element in points.descendants() if element.classes), None)
    found = re.fullmatch(r"(-?\d+)(/(\d*))?", wording)
    if found is None or (icon is None) == bool(found[2]):
        raise ValueError(f"unknown Victory Points {wording!r}")
    if icon is None:
        return int(wording)
    amount, per = int(found[1]), int(found[3] or 1)
    counted = _counted_for_victory_points(icon, text)
    if "card_resource" in counted and "one or more" in text:
        return {"points": amount, "at_least": 1, "of": counted}
    return {"points": amount, "per": per, "of": counted}


def _counted_for_victory_points(icon: Element, text: str) -> dict[str, str]:
    """What Victory Points count: Card Resources on the card, the Player's Tags, Tiles next to
    the card's own Tile, or Tiles in play."""
    if icon.has_class("resource-tag"):
        return {"tag": _named(icon, "tag-")}
    if card_resource := next((name for name in CARD_RESOURCES if icon.has_class(name)), None):
        return {"card_resource": card_resource}
    tiles = {"ocean-resource": "ocean", "city-tile-small": "city"}
    tile = next((tiles[name] for name in icon.classes if name in tiles), None)
    # The icon alone doesn't say which Tiles count; the text does.
    if tile and "adjacent" in text.lower():
        return {"adjacent": tile}
    if tile and "in play" in text.lower():
        return {"tiles_in_play": tile}
    raise ValueError(f"unknown Victory Points for {' '.join(icon.classes)!r}")


def _named(element: Element, prefix: str) -> str:
    """The rest of `element`'s class that starts with `prefix`: "space" for "tag-space"."""
    return next(name.removeprefix(prefix) for name in element.classes if name.startswith(prefix))


def _text(content: Element) -> str:
    """The card's printed text: one line for each paragraph of its descriptions, or of its
    middle part if it has none."""
    descriptions = content.outermost("description")
    paragraphs = [line for description in descriptions for line in _paragraphs(description)]
    return "\n".join(paragraphs or _paragraphs(content))


# Stands for a line break in a description while its text is pieced together.
_LINE_BREAK = object()


def _paragraphs(description: Element) -> list[str]:
    """The paragraphs of a description. Two line breaks in a row start a new paragraph; a
    single one only wraps a line to fit the card. A description inside it is part of it. What
    is drawn as an icon (an element with another class, or a background) is not part of the text."""
    pieces: list[Any] = []

    def collect(element: Element) -> None:
        for child in element.children:
            if isinstance(child, str):
                pieces.append(HTML_WHITESPACE.sub(" ", child))
            elif child.tag == "br":
                pieces.append(_LINE_BREAK)
            elif child.has_class("description") or not (child.classes or "background" in child.style):
                pieces.append(" ")
                collect(child)
                pieces.append(" ")

    collect(description)
    text = ""
    breaks = 0
    for piece in pieces:
        if piece is _LINE_BREAK:
            breaks += 1
            continue
        if breaks and not piece.strip(" "):
            continue  # only whitespace between line breaks
        text += "\n" if breaks >= 2 else " " if breaks else ""
        text += piece
        breaks = 0
    # In the text, a no-break space is just a space.
    lines = (re.sub(" +", " ", line.replace("\xa0", " ")).strip(" ") for line in text.split("\n"))
    return [line for line in lines if line]


def _face(content: Element, title: Element | None = None) -> dict[str, Any]:
    """What the GUI needs to draw the card as the card list does, beyond its printed data:
    the card's middle part, and the title's own style where it has one."""
    face: dict[str, Any] = {"content": _node(content)}
    if title is not None and title.style:
        face["title_style"] = title.style
    return face


def _node(element: Element) -> dict[str, Any]:
    """An element as plain data: its tag, class, inline style and children, each left out
    when empty. Text is a string, with each run of whitespace collapsed to one space, as a
    browser shows it; where a space falls, at the start or end of an element, is kept."""
    node: dict[str, Any] = {"tag": element.tag}
    if element.classes:
        node["class"] = " ".join(element.classes)
    if element.style:
        node["style"] = element.style
    children = [
        HTML_WHITESPACE.sub(" ", child) if isinstance(child, str) else _node(child) for child in element.children
    ]
    if children:
        node["children"] = children
    return node


def keep_written_by_hand(
    imported: list[dict[str, Any]], *, earlier: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """The imported cards, each with any fields written by hand on the same card in `earlier`."""
    imported_ids = {card["id"] for card in imported}
    written_by_hand = {
        card["id"]: {name: value for name, value in card.items() if name not in PRINTED_FIELDS}
        for card in earlier
    }
    lost = [card_id for card_id, fields in written_by_hand.items() if fields and card_id not in imported_ids]
    if lost:
        raise ValueError(
            f"these cards have data written by hand but are no longer on the card list: {', '.join(lost)}"
        )
    return [{**card, **written_by_hand.get(card["id"], {})} for card in imported]


def card_file_text(cards: list[dict[str, Any]]) -> str:
    """The card file: JSON with one line for each field of each card, so that a change to
    one card shows as a change to its lines."""
    entries = []
    for card in cards:
        lines = [f"      {json.dumps(name)}: {json.dumps(value, ensure_ascii=False)}" for name, value in card.items()]
        entries.append("    {\n" + ",\n".join(lines) + "\n    }")
    about = f'  "about": {json.dumps(ABOUT_THE_CARD_FILE)}'
    return "{\n" + about + ',\n  "cards": [\n' + ",\n".join(entries) + "\n  ]\n}\n"


def icons_used(html: str, stylesheet: str) -> list[str]:
    """The images and fonts the catalog's cards need, as paths on the card list site: those of every
    style rule all of whose classes some catalog card uses, plus the fonts."""
    used = set()
    for item in _catalog_cards(parse_html(html)):
        used.update(item.classes, *(element.classes for element in item.descendants()))
    paths = set()
    for rule in re.finditer(r"([^{}]+)\{([^{}]*)\}", _without_comments(stylesheet)):
        selectors, declarations = rule[1].strip(), rule[2]
        needed = selectors == "@font-face" or any(
            (classes := re.findall(r"\.([\w-]+)", selector)) and used.issuperset(classes)
            for selector in selectors.split(",")
        )
        if needed:
            paths.update(re.findall(r"url\(\s*[\"']?(?:\.\./)?([^\"')]+)", declarations))
    return sorted(paths)


def import_cards() -> list[dict[str, Any]]:
    """Parses the saved page, checks that it gives the whole card set, keeps what was written
    by hand, and writes the card file."""
    imported = parse_card_list(PAGE.read_text(encoding="utf-8"))
    check_card_set(imported)
    earlier = json.loads(CARD_FILE.read_text(encoding="utf-8"))["cards"] if CARD_FILE.exists() else []
    cards = keep_written_by_hand(imported, earlier=earlier)
    CARD_FILE.parent.mkdir(exist_ok=True)
    CARD_FILE.write_text(card_file_text(cards), encoding="utf-8")
    return cards


def check_card_set(cards: list[dict[str, Any]]) -> None:
    """Refuses a card list that no longer gives every card of the catalog, in the catalog's order."""

    def numbers(expansion: str, card_types: tuple[str, ...]) -> list[int]:
        return [card["number"] for card in cards if card["expansion"] == expansion and card["type"] in card_types]

    def corporations(expansion: str) -> int:
        return len(numbers(expansion, ("corporation",)))

    project_cards = ("automated", "active", "event")
    prelude_project_cards = range(PRELUDE_CARDS + 1, PRELUDE_CARDS + PRELUDE_PROJECT_CARDS + 1)
    in_prelude = sum(card["expansion"] == "prelude" for card in cards)
    if numbers("base", project_cards) != list(range(1, PROJECT_CARDS + 1)) or corporations("base") != CORPORATIONS:
        raise ValueError(
            f"expected Project Cards #001 to #{PROJECT_CARDS:03} in order and {CORPORATIONS} Corporations, "
            f"found {len(numbers('base', project_cards))} Project Cards and {corporations('base')} Corporations"
        )
    if (
        numbers("prelude", ("prelude",)) != list(range(1, PRELUDE_CARDS + 1))
        or numbers("prelude", project_cards) != list(prelude_project_cards)
        or corporations("prelude") != PRELUDE_CORPORATIONS
    ):
        raise ValueError(
            f"expected {PRELUDE_CARDS} Prelude Cards, {PRELUDE_PROJECT_CARDS} Project Cards and "
            f"{PRELUDE_CORPORATIONS} Corporations in Prelude, found {in_prelude} cards of Prelude"
        )


def download() -> None:
    """Fetches the card list page and its stylesheet into the snapshot, and the icons the
    catalog's cards use into the GUI."""
    PAGE.write_bytes(fetch(PAGE_URL))
    STYLESHEET.write_bytes(fetch(STYLESHEET_URL))
    for path in icons_used(PAGE.read_text(encoding="utf-8"), STYLESHEET.read_text(encoding="utf-8")):
        (ICONS / path).parent.mkdir(parents=True, exist_ok=True)
        (ICONS / path).write_bytes(fetch(SITE + path))
        print(f"fetched {path}")


def fetch(url: str) -> bytes:
    """What is at `url`, for the tools that download."""
    with urllib.request.urlopen(url, timeout=30) as response:
        return response.read()


def main() -> None:
    parser = argparse.ArgumentParser(description="Import the printed card data from the fan-made card list.")
    parser.add_argument(
        "--download", action="store_true", help="fetch the card list page, its stylesheet and the icons first"
    )
    if parser.parse_args().download:
        download()
    cards = import_cards()
    corporations = sum(card["type"] == "corporation" for card in cards)
    prelude_cards = sum(card["type"] == "prelude" for card in cards)
    project_cards = len(cards) - corporations - prelude_cards
    print(
        f"Wrote {project_cards} Project Cards, {corporations} Corporations and {prelude_cards} Prelude Cards "
        f"to {CARD_FILE.relative_to(PROJECT)}."
    )


if __name__ == "__main__":
    main()
