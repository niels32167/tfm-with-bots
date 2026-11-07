"""Compares our card file with the open-source game's card definitions (ADR 0005) and writes
the mismatch report, `docs/card-mismatches.md`:

    uv run python -m tools.card_mismatches              # from the saved copy of the definitions
    uv run python -m tools.card_mismatches --download   # fetch them first

The fields compared are the ones the card list could get wrong and the rules depend on:
Corporate Era, the box a card comes in, type, cost, Tags, Requirements and Victory Points, and a
Corporation's starting MegaCredits, which our effect data holds. Each difference is then
settled by the rules authority order (rulebook, FryxGames FAQ, then the open-source game);
see `docs/rules-notes.md`.

The open-source game is GPL-3.0, so its files are kept out of the repository, in
`.cache/open-source-cards/<commit>/` (ignored by git). The report names the commit.
"""

import argparse
import json
import re
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import tm_engine

from tools.card_import import PROJECT, card_id, fetch, printed_number

REPORT = PROJECT / "docs" / "card-mismatches.md"
CACHE = PROJECT / ".cache" / "open-source-cards"

REPOSITORY = "terraforming-mars/terraforming-mars"
# The commit compared against; `--commit` picks another.
COMMIT = "4d30aa07f14eeb5aa5647775ce5a7c9e49f6ac04"
CARD_FOLDERS = ("src/server/cards/base", "src/server/cards/corporation", "src/server/cards/prelude")
PRELUDE_FOLDER = "prelude"
MANIFESTS = "src/server/cards/StandardCardManifests.ts"

# The fields compared, in the report's order.
COMPARED_FIELDS = (
    "corporate_era",
    "expansion",
    "type",
    "cost",
    "tags",
    "requirements",
    "victory_points",
    "starting_megacredits",
)

# Our names that differ from the open-source game's on purpose, each with the evidence for it in
# docs/rules-notes.md, and the open-source game's name for the card.
NAMES_SETTLED = {"Allied Banks": "ALLIED_BANK", "Biolabs": "BIOLAB", "Excentric Sponsor": "ECCENTRIC_SPONSOR"}
# The Triggers a Corporation sets off when it is revealed: Vitor's, for a card with Victory Points.
SET_OFF_BY_THE_CORPORATION_ITSELF = ("card_with_victory_points",)


@dataclass(frozen=True)
class Mismatch:
    card: str
    field: str
    ours: Any
    theirs: Any


@dataclass
class Comparison:
    mismatches: list[Mismatch] = field(default_factory=list)
    # Fields the open-source game works out in code, so there is nothing to compare.
    not_compared: list[str] = field(default_factory=list)
    # Our card and the open-source game's name for it, where they differ and nobody has settled it.
    names_that_differ: list[tuple[str, str]] = field(default_factory=list)
    # The same, where the rules notes have settled it: those in NAMES_SETTLED.
    names_settled: list[tuple[str, str]] = field(default_factory=list)
    # Our cards the open-source game has no definition for.
    missing: list[str] = field(default_factory=list)


def parse_open_source_card(
    source: str, file_name: str, *, base_classes: dict[str, str] | None = None
) -> dict[str, Any] | None:
    """A card definition from the open-source game, with its fields in our card file's form,
    or None if the file defines no card. Its name is the game's own constant for it, such
    as "COLONIZER_TRAINING_CAMP".

    A card usually passes its fields to `super({...})`. A few take some from constructor
    defaults (`cost = 12`), or pass them positionally to a base class in `base_classes`
    (class name to source), whose own `super({...})` holds the rest.
    """
    if re.search(r"\babstract class\b", source):
        return None  # a base class for cards, not a card
    fields = _super_fields(source)
    if fields is None:
        fields = _inherited_fields(source, base_classes or {})
    if fields is None:
        return None
    fields = {name: value or _default(source, name) for name, value in fields.items()}
    if "startingMegaCredits" in fields:
        card_type = "corporation"
    elif re.search(r"\bextends PreludeCard\b", source):
        card_type = "prelude"  # its base class gives the type
    elif found := re.fullmatch(r"CardType\.(\w+)", fields.get("type", "")):
        card_type = found[1].lower()
    else:
        return None
    name = re.search(r"\bname\s*[:=]\s*CardName\.(\w+)", source)
    number = re.search(r"cardNumber:\s*'(\w+)'", source)
    card_resource = re.fullmatch(r"CardResource\.(\w+)", fields.get("resourceType", ""))
    starting = {"starting_megacredits": int(fields["startingMegaCredits"])} if card_type == "corporation" else {}
    return {
        "number": _number(number[1]) if number else None,
        "name": name[1] if name else Path(file_name).stem,
        "type": card_type,
        "cost": int(fields["cost"]) if "cost" in fields else None,
        "tags": [tag.lower() for tag in re.findall(r"Tag\.(\w+)", fields.get("tags", ""))],
        "requirements": _requirements(fields.get("requirements", "")),
        "victory_points": _victory_points(fields.get("victoryPoints", ""), card_resource),
        **starting,
    }


def _number(written: str) -> int | str | None:
    """A card's number: 64 for "064", and "P36" for Prelude's. Other forms are not printed numbers."""
    if written.isdigit():
        return int(written)
    return written if re.fullmatch(r"P\d+", written) else None


def _super_fields(source: str) -> dict[str, str] | None:
    start = source.find("super({")
    return None if start == -1 else _fields(_enclosed(source, start + len("super(")))


def _inherited_fields(source: str, base_classes: dict[str, str]) -> dict[str, str] | None:
    """The fields of a card whose base class takes them as constructor arguments."""
    parent = re.search(r"\bextends (\w+)", source)
    start = source.find("super(")
    if parent is None or parent[1] not in base_classes or start == -1:
        return None
    base = base_classes[parent[1]]
    fields = _super_fields(base)
    constructor = base.find("constructor(")
    if fields is None or constructor == -1:
        return None
    parameters = [part.partition(":")[0].strip() for part in _split(_enclosed(base, constructor + len("constructor")))]
    arguments = _split(_enclosed(source, start + len("super")))
    passed = dict(zip(parameters, arguments, strict=False))
    return {name: value or passed.get(name, "") for name, value in fields.items()}


def _default(source: str, name: str) -> str:
    """The default value a constructor gives a parameter, as written: `cost = 12` gives "12"."""
    found = re.search(rf"\b{name}\s*=\s*([^,\n)]+)", source)
    return found[1].strip() if found else ""


def corporate_era_classes(manifests: str) -> set[str]:
    """The card classes the open-source game's Corporate Era manifest lists."""
    corporate_era = re.search(r"CORP_ERA_CARD_MANIFEST\s*=\s*new ModuleManifest\(", manifests)
    if corporate_era is None:
        raise ValueError("the card manifests have no Corporate Era manifest")
    return set(re.findall(r"Factory:\s*(\w+)", _enclosed(manifests, corporate_era.end())))


def _scan(text: str, start: int = 0) -> Iterator[tuple[int, int]]:
    """Each position from `start` that is code (not inside a string or comment), with its
    depth of brackets."""
    depth = 0
    position = start
    while position < len(text):
        if text.startswith("//", position):
            position = _after(text, "\n", position)
            continue
        if text.startswith("/*", position):
            position = _after(text, "*/", position)
            continue
        character = text[position]
        if character in "'\"`":
            end = position + 1
            while end < len(text) and text[end] != character:
                end += 2 if text[end] == "\\" else 1
            position = end + 1
            continue
        if character in ")]}":
            depth -= 1
        yield position, depth
        if character in "([{":
            depth += 1
        position += 1


def _after(text: str, ending: str, position: int) -> int:
    found = text.find(ending, position)
    return len(text) if found == -1 else found + len(ending)


def _enclosed(text: str, opening: int) -> str:
    """What is inside the bracket at `opening`, up to its matching closing bracket."""
    for position, depth in _scan(text, opening):
        if depth == 0 and position > opening and text[position] in ")]}":
            return text[opening + 1 : position]
    raise ValueError(f"no closing bracket for {text[opening:opening + 40]!r}")


def _split(text: str) -> list[str]:
    """The comma-separated parts of `text`, ignoring commas inside brackets and strings."""
    parts, start = [], 0
    for position, depth in _scan(text):
        if depth == 0 and text[position] == ",":
            parts.append(text[start:position])
            start = position + 1
    parts.append(text[start:])
    return [part.strip() for part in parts if part.strip()]


def _fields(text: str) -> dict[str, str]:
    """The fields of an object's inside, {name: written value}. A shorthand field such as
    `max` has an empty value."""
    fields = {}
    for part in _split(text):
        name, _, value = part.partition(":")
        fields[name.strip()] = value.strip()
    return fields


def _objects(written: str) -> list[dict[str, str]]:
    """An object `{...}` or a list of them, as the fields of each."""
    written = written.strip()
    if written.startswith("["):
        return [_fields(_enclosed(part, 0)) for part in _split(_enclosed(written, 0))]
    return [_fields(_enclosed(written, 0))] if written.startswith("{") else []


def _requirements(written: str) -> list[dict[str, Any]]:
    return [_requirement(fields) for fields in _objects(written)]


def _requirement(fields: dict[str, str]) -> dict[str, Any]:
    limit = "max" if "max" in fields else "min"
    for parameter in ("oxygen", "temperature", "oceans"):
        if parameter in fields:
            return {"type": parameter, limit: int(fields[parameter])}
    count = int(fields.get("count", 1))
    if "tag" in fields:
        return {"type": "tag", "tag": _member(fields["tag"]), "min": count}
    if "production" in fields:
        return {"type": "production", "resource": _member(fields["production"]), "min": count}
    owner = "anyone" if "all" in fields else "you"
    for written, tile in (("greeneries", "greenery"), ("cities", "city")):
        if written in fields:
            return {"type": "tiles", "tile": tile, "owner": owner, "min": int(fields[written])}
    return {"type": "unknown", "written": fields}


def _victory_points(written: str, card_resource: re.Match[str] | None) -> Any:
    """Victory Points in our card file's form; "special" when the open-source game works them
    out in code, and {"unknown": ...} for a form this doesn't read, so the report shows it."""
    if not written:
        return None
    if re.fullmatch(r"-?\d+", written):
        return int(written)
    if written.strip("'\"") == "special":
        return "special"
    [fields] = _objects(written) or [{}]
    points, per = int(fields.get("each", 1)), int(fields.get("per", 1))
    if "resourcesHere" in fields and card_resource:
        counted = {"card_resource": card_resource[1].lower()}
    elif "tag" in fields:
        counted = {"tag": _member(fields["tag"])}
    elif "nextToThis" in fields:
        counted = {"adjacent": "ocean" if "oceans" in fields else "city"}
    elif "cities" in fields and "all" in fields:
        counted = {"tiles_in_play": "city"}
    else:
        return {"unknown": written}
    return {"points": points, "per": per, "of": counted}


def _member(written: str) -> str:
    """The member an enum value names, as we name it: "science" for `Tag.SCIENCE`."""
    return written.rpartition(".")[2].lower()


def compare(ours: list[dict[str, Any]], theirs: list[dict[str, Any]]) -> Comparison:
    """How our cards differ from the open-source game's. Project Cards and Prelude Cards are paired
    by number, Corporations by name."""
    def their_key(card: dict[str, Any]) -> Any:
        return card["number"] if card["type"] != "corporation" else card["name"]

    def our_key(card: dict[str, Any]) -> Any:
        if card["type"] == "corporation":
            return card_id(card["name"]).upper()
        return printed_number(card).removeprefix("#") if card["expansion"] == "prelude" else card["number"]

    their_cards = {their_key(card): card for card in theirs}
    comparison = Comparison()
    for our_card in ours:
        label = _label(our_card)
        their_card = their_cards.get(our_key(our_card))
        if their_card is None:
            comparison.missing.append(label)
            continue
        if card_id(our_card["name"]).upper() != their_card["name"]:
            settled = NAMES_SETTLED.get(our_card["name"]) == their_card["name"]
            names = comparison.names_settled if settled else comparison.names_that_differ
            names.append((label, their_card["name"]))
        for name in COMPARED_FIELDS:
            if name not in their_card:
                continue
            if name == "victory_points" and their_card[name] == "special":
                comparison.not_compared.append(f"{label}: the open-source game works out its Victory Points in code")
                continue
            if name == "starting_megacredits" and "effects" not in our_card:
                comparison.not_compared.append(
                    f"{label}: not implemented yet, so its starting MegaCredits have no effect data"
                )
                continue
            our_value, their_value = _comparable(name, our_card), _comparable(name, their_card)
            if our_value != their_value:
                comparison.mismatches.append(Mismatch(label, name, our_value, their_value))
    return comparison


def _label(card: dict[str, Any]) -> str:
    number = printed_number(card)
    return card["name"] if number is None else f"{number} {card['name']}"


def _comparable(name: str, card: dict[str, Any]) -> Any:
    """A field of `card` in a form where order doesn't matter, where it doesn't on the card. Our
    Corporations have their starting MegaCredits in their effect data, plus what a Trigger set off by the
    Corporation itself gives them when it is revealed (Vitor's 3, "including this"), which the open-source
    game adds to what it starts with."""
    if name == "starting_megacredits" and name not in card:
        effects = card.get("effects", {})
        for_itself = sum(
            trigger.get("resources", {}).get("megacredits", 0)
            for trigger in effects.get("when", [])
            if trigger["on"] in SET_OFF_BY_THE_CORPORATION_ITSELF
        )
        return effects.get("resources", {}).get("megacredits", 0) + for_itself
    value = card[name]
    if name == "tags":
        # The open-source game leaves the Event Tag out of an Event card's Tags.
        if card["type"] == "event" and "event" not in value:
            value = [*value, "event"]
        return sorted(value)
    if name == "requirements":
        return sorted(value, key=json.dumps)
    return value


def report(comparison: Comparison, *, commit: str) -> str:
    """The mismatch report, in Markdown."""
    lines = [
        "# Card data mismatches",
        "",
        "The printed card data imported from the fan-made card list (`engine/cards/cards.json`),",
        f"compared with the open-source game's card definitions ([{REPOSITORY}](https://github.com/{REPOSITORY})",
        f"at commit `{commit}`). Written by `uv run python -m tools.card_mismatches`; do not edit by hand.",
        "",
        "Compared: Corporate Era, the box a card comes in, type, cost, Tags (in any order),",
        "Requirements (in any order), Victory Points, and a Corporation's starting MegaCredits (with",
        "what its own Trigger gives it when revealed, as Vitor's 3), for",
        "the cards of the base box and of Prelude. The open-source game leaves the Event Tag out of",
        "an Event card's Tags, so the comparison adds it back. Each difference is",
        "settled by the rules authority order (rulebook, then the FryxGames FAQ, then the open-source",
        "game), and the call is recorded in `docs/rules-notes.md`.",
        "",
        f"## Differences ({len(comparison.mismatches)})",
        "",
    ]
    if comparison.mismatches:
        lines += ["| Card | Field | Card list | Open-source game |", "| --- | --- | --- | --- |"]
        lines += [
            f"| {mismatch.card} | {mismatch.field} | {_shown(mismatch.ours)} | {_shown(mismatch.theirs)} |"
            for mismatch in comparison.mismatches
        ]
    else:
        lines.append("None.")
    lines += ["", f"## Not compared ({len(comparison.not_compared)})", ""]
    lines += [f"- {line}" for line in comparison.not_compared] or ["None."]
    lines += ["", f"## Names that differ ({len(comparison.names_that_differ)})", ""]
    lines += [f"- {ours}: `{theirs}`" for ours, theirs in comparison.names_that_differ] or ["None."]
    lines += ["", f"## Names settled in the rules notes ({len(comparison.names_settled)})", ""]
    lines += [f"- {ours}: `{theirs}`" for ours, theirs in comparison.names_settled] or ["None."]
    lines += ["", f"## Missing from the open-source game ({len(comparison.missing)})", ""]
    lines += [f"- {card}" for card in comparison.missing] or ["None."]
    return "\n".join(lines) + "\n"


def _shown(value: Any) -> str:
    if value is None:
        return "—"
    return f"`{json.dumps(value)}`" if isinstance(value, list | dict) else json.dumps(value)


def load_open_source_cards(commit: str) -> list[dict[str, Any]]:
    """The open-source game's card definitions saved for `commit`, in the catalog's sets, with
    Corporate Era and the box each comes in marked."""
    folder = CACHE / commit
    corporate_era = corporate_era_classes((folder / Path(MANIFESTS).name).read_text(encoding="utf-8"))
    sources = {path.stem: path.read_text(encoding="utf-8") for path in sorted(folder.glob("*/*.ts"))}
    cards = []
    for path in sorted(folder.glob("*/*.ts")):
        try:
            card = parse_open_source_card(sources[path.stem], path.name, base_classes=sources)
        except ValueError as problem:
            raise ValueError(f"{path.relative_to(folder)}: {problem}") from None
        if card is not None:
            expansion = "prelude" if path.parent.name == PRELUDE_FOLDER else "base"
            cards.append({**card, "corporate_era": path.stem in corporate_era, "expansion": expansion})
    return cards


def download(commit: str) -> None:
    """Fetches the open-source game's card definitions and manifests at `commit`, except any
    already saved: a commit's files never change."""
    folder = CACHE / commit
    for card_folder in CARD_FOLDERS:
        saved = folder / Path(card_folder).name
        listing = json.loads(fetch(f"https://api.github.com/repos/{REPOSITORY}/contents/{card_folder}?ref={commit}"))
        saved.mkdir(parents=True, exist_ok=True)
        for entry in listing:
            is_a_definition = entry["type"] == "file" and entry["name"].endswith(".ts")
            if is_a_definition and not (saved / entry["name"]).exists():
                (saved / entry["name"]).write_bytes(fetch(_raw(commit, entry["path"])))
    (folder / Path(MANIFESTS).name).write_bytes(fetch(_raw(commit, MANIFESTS)))


def _raw(commit: str, path: str) -> str:
    return f"https://raw.githubusercontent.com/{REPOSITORY}/{commit}/{path}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare the card file with the open-source game's cards.")
    parser.add_argument(
        "--download", action="store_true", help="fetch the open-source game's card definitions first"
    )
    parser.add_argument(
        "--commit", default=COMMIT, help=f"the open-source game's commit to compare with (default {COMMIT})"
    )
    arguments = parser.parse_args()
    if arguments.download:
        download(arguments.commit)
    comparison = compare(tm_engine.card_catalog(), load_open_source_cards(arguments.commit))
    REPORT.write_text(report(comparison, commit=arguments.commit), encoding="utf-8")
    print(f"{len(comparison.mismatches)} differences written to {REPORT.relative_to(PROJECT)}.")


if __name__ == "__main__":
    main()
