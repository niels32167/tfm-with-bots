"""Names in Recorded Games, mapped to the card catalog's ids and the engine's Milestone and Award ids.

Board Game Arena's names differ from the catalog's in spelling ("Allied Bank" for Allied Banks), and the
scraper sometimes failed to translate a name, leaving an internal one ("card_prelude_P34") or a Polish
one ("Bankier"). A name that maps to nothing here is outside what this project plays (another
expansion or map, or the Beginner Corporation), or a new variant, which the importer reports.
"""

import json
import re
import unicodedata
from functools import cache
from pathlib import Path
from typing import Any

# The card catalog as the engine embeds it. Read as a file, so that nothing in ai/ but the Controller seam
# and the Match tool imports the engine (tests/ai/test_fair_play.py).
CATALOG_FILE = Path(__file__).parents[2] / "engine" / "cards" / "cards.json"

# Board Game Arena's spellings that differ from the catalog's by more than case and punctuation.
CARD_ALIASES = {
    "alliedbank": "allied_banks",
    "ceosfavouriteproject": "ceos_favorite_project",
    "eccentricsponsor": "excentric_sponsor",
}

UNTRANSLATED_PRELUDE = re.compile(r"card_prelude_P(\d+)")

MILESTONES = {
    "terraformer": "terraformer",
    "mayor": "mayor",
    "gardener": "gardener",
    "builder": "builder",
    "planner": "planner",
}

AWARDS = {
    "landlord": "landlord",
    "banker": "banker",
    "scientist": "scientist",
    "thermalist": "thermalist",
    "miner": "miner",
    # Untranslated, in Polish.
    "potentatziemski": "landlord",
    "bankier": "banker",
    "naukowiec": "scientist",
    "magnatcieplny": "thermalist",
    "gornik": "miner",
}


def squeeze(name: str) -> str:
    """The name in lower case, with accents, spaces and punctuation left out."""
    plain = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return "".join(character for character in plain.lower() if character.isalnum())


@cache
def catalog() -> list[dict[str, Any]]:
    cards = json.loads(CATALOG_FILE.read_text(encoding="utf-8"))
    return cards if isinstance(cards, list) else cards["cards"]


@cache
def catalog_ids() -> dict[str, str]:
    return {squeeze(card["name"]): card["id"] for card in catalog()}


@cache
def prelude_card_ids() -> dict[int, str]:
    return {card["number"]: card["id"] for card in catalog() if card["type"] == "prelude"}


def card_id(name: str) -> str | None:
    """The catalog id of the card a Recorded Game names, or None if the catalog has no such card."""
    untranslated = UNTRANSLATED_PRELUDE.fullmatch(name)
    if untranslated:
        return prelude_card_ids().get(int(untranslated.group(1)))
    key = squeeze(name)
    return catalog_ids().get(key) or CARD_ALIASES.get(key)


def milestone_id(name: str) -> str | None:
    """The engine's id of a Tharsis Milestone a Recorded Game names, or None for another map's."""
    return MILESTONES.get(squeeze(name))


def award_id(name: str) -> str | None:
    """The engine's id of a Tharsis Award a Recorded Game names, or None for another map's."""
    return AWARDS.get(squeeze(name))
