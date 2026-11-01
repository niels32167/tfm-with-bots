"""The Tharsis board: every Area, what it is reserved for, and its placement bonus."""

import tm_engine

from tests.helpers import area, areas_on_mars

# The official Tharsis board, row by row from the top and each row from the left. Rows
# are lettered A to J, skipping I, as the open-source game labels them. Each Area is
# written as its placement bonus, one letter per item (s steel, t titanium, p plant,
# c card) or "." for none, with "~" in front if the Area is reserved for an Ocean.
THARSIS = {
    "A": "ss  ~ss  .    ~c   ~",
    "B": ".   s    .    .    .    ~cc",
    "C": "c   .    .    .    .    .    s",
    "D": "pt  p    p    p    pp   p    p    ~pp",
    "E": "pp  pp   pp   ~pp  ~pp  ~pp  pp   pp   pp",
    "F": "p   pp   p    p    p    ~p   ~p   ~p",
    "G": ".   .    .    .    .    p    .",
    "H": "ss  .    c    c    .    t",
    "J": "s   ss   .    .    ~tt",
}
BONUS_ITEMS = {"s": "steel", "t": "titanium", "p": "plant", "c": "card"}

# The four volcanoes and Noctis City are named on the board.
NAMES = {"B2": "Tharsis Tholus", "C1": "Ascraeus Mons", "D1": "Pavonis Mons", "E1": "Arsia Mons", "E3": "Noctis City"}


def printed_area(letter: str, row: int, position: int, printed: str) -> dict:
    identifier = f"{letter}{position}"
    return {
        "area": identifier,
        "name": NAMES.get(identifier),
        "row": row,
        "position": position,
        "reserved": "ocean" if printed.startswith("~") else None,
        "bonus": [BONUS_ITEMS[item] for item in printed.lstrip("~").replace(".", "")],
        "tile": None,
        "claimed_by": None,
    }


def test_every_area_on_mars_matches_the_official_tharsis_board():
    expected = [
        printed_area(letter, row, position, printed)
        for row, (letter, areas) in enumerate(THARSIS.items(), start=1)
        for position, printed in enumerate(areas.split(), start=1)
    ]
    expected[[entry["area"] for entry in expected].index("E3")]["reserved"] = "noctis_city"

    assert areas_on_mars(tm_engine.Game(seed=1)) == expected


def test_mars_has_61_areas_of_which_12_are_reserved_for_oceans():
    on_mars = areas_on_mars(tm_engine.Game(seed=1))

    assert len(on_mars) == 61
    reserved_for_oceans = [entry["area"] for entry in on_mars if entry["reserved"] == "ocean"]
    assert reserved_for_oceans == ["A2", "A4", "A5", "B6", "D8", "E4", "E5", "E6", "F6", "F7", "F8", "J5"]


def test_noctis_city_is_reserved_for_its_card():
    noctis_city = area(tm_engine.Game(seed=1), "E3")

    assert noctis_city["name"] == "Noctis City"
    assert noctis_city["reserved"] == "noctis_city"


def test_phobos_space_haven_and_ganymede_colony_are_areas_off_mars_reserved_for_their_cards():
    game = tm_engine.Game(seed=1)

    assert area(game, "phobos_space_haven") == {
        "area": "phobos_space_haven",
        "name": "Phobos Space Haven",
        "row": None,
        "position": None,
        "reserved": "phobos_space_haven",
        "bonus": [],
        "tile": None,
        "claimed_by": None,
    }
    assert area(game, "ganymede_colony")["name"] == "Ganymede Colony"
    assert area(game, "ganymede_colony")["reserved"] == "ganymede_colony"


def test_a_new_game_starts_with_no_tiles_oxygen_at_0_and_no_oceans():
    view = tm_engine.Game(seed=1).player_view(0)

    assert all(entry["tile"] is None for entry in view["board"])
    assert view["oxygen"] == 0
    assert view["oceans"] == 0
