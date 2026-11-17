"""A Recorded Game's setup, Draft and buy records as the Decisions the engine would ask (ticket 12 of phase 2):
the same Player View, Options and pick, with what the records don't hold left out, so that a position in the
dataset and the same position in the engine encode alike."""

import random

import tm_engine

from ai.encoding import (
    AWARDS,
    CARD_FIELDS,
    GLOBAL_FIELDS,
    MILESTONES,
    OPTION_FIELDS,
    RESOURCES,
    TAGS,
    ZONES,
    Encoding,
    encode,
)
from ai.recorded_games.records import as_recorded, recorded_decisions

ZERO = dict.fromkeys(RESOURCES, 0)
NO_TAGS = dict.fromkeys(TAGS, 0)
UNSET = {"terraform_rating": 20, "resources": ZERO, "production": ZERO, "tags": NO_TAGS, "events": 0}

# Seed 7 with Prelude, written as the importer writes a Recorded Game (ai/recorded_games/__init__.py): Player 2
# goes first. Both keep their first two Prelude Cards and buy two cards at setup, play their Prelude Cards and
# pass, then draft and buy one card each in Generation 2. Offers are in the order a Board Game Arena log might
# list them, not the engine's, and the Hand Counters are stale, as they often are.
GAME = {
    "game": "example",
    "prelude": True,
    "players": [{"corporation": "credicor"}, {"corporation": "thorgate"}],
    "positions": [
        {
            "generation": 1,
            "temperature": -30,
            "oxygen": 0,
            "oceans": 0,
            "milestones": {},
            "awards": {},
            "players": [
                {**UNSET, "corporation": None, "hand_counter": None, "played": [], "prelude_cards": []},
                {**UNSET, "corporation": None, "hand_counter": None, "played": [], "prelude_cards": []},
            ],
        },
        {
            "generation": 2,
            "temperature": -30,
            "oxygen": 1,
            "oceans": 0,
            "milestones": {},
            "awards": {},
            "players": [
                {
                    "corporation": "credicor",
                    "terraform_rating": 20,
                    "resources": ZERO | {"megacredits": 78, "plants": 3, "energy": 1},
                    "production": ZERO | {"megacredits": 4, "plants": 1, "energy": 1},
                    "tags": NO_TAGS | {"earth": 1, "microbe": 1},
                    "events": 0,
                    "hand_counter": 3,
                    "played": [],
                    "prelude_cards": ["biofuels", "allied_banks"],
                },
                {
                    "corporation": "thorgate",
                    "terraform_rating": 21,
                    "resources": ZERO | {"megacredits": 84, "steel": 2, "energy": 1},
                    "production": ZERO | {"energy": 1},
                    "tags": NO_TAGS | {"power": 1, "plant": 1},
                    "events": 0,
                    "hand_counter": 5,
                    "played": [],
                    "prelude_cards": ["experimental_forest", "donation"],
                },
            ],
        },
    ],
    "decisions": [
        {
            "kind": "setup",
            "player": 1,
            "generation": 1,
            "position": 0,
            "offer": {
                "corporations": ["teractor", "thorgate"],
                "prelude_cards": ["smelting_plant", "donation", "experimental_forest", "power_generation"],
                "cards": [
                    "house_printing",
                    "martian_rails",
                    "ghg_producing_bacteria",
                    "grass",
                    "steelworks",
                    "artificial_photosynthesis",
                    "industrial_center",
                    "symbiotic_fungus",
                    "pets",
                    "heat_trappers",
                ],
            },
            "picked": {
                "corporation": "thorgate",
                "prelude_cards": ["experimental_forest", "donation"],
                "cards": ["ghg_producing_bacteria", "martian_rails"],
            },
        },
        {
            "kind": "setup",
            "player": 0,
            "generation": 1,
            "position": 0,
            "offer": {
                "corporations": ["credicor", "united_nations_mars_initiative"],
                "prelude_cards": ["allied_banks", "biofuels", "early_settlement", "orbital_construction_yard"],
                "cards": [
                    "underground_city",
                    "nuclear_power",
                    "quantum_extractor",
                    "open_city",
                    "geothermal_power",
                    "urbanized_area",
                    "ecological_zone",
                    "restricted_area",
                    "underground_detonations",
                    "ai_central",
                ],
            },
            "picked": {
                "corporation": "credicor",
                "prelude_cards": ["allied_banks", "biofuels"],
                "cards": ["underground_city", "nuclear_power"],
            },
        },
        {
            "kind": "draft",
            "player": 0,
            "generation": 2,
            "position": 1,
            "pick": 1,
            "offer": ["technology_demonstration", "electro_catapult", "giant_ice_asteroid", "ice_cap_melting"],
            "picked": "electro_catapult",
            "drafted": [],
            "passed": [],
        },
        {
            "kind": "draft",
            "player": 1,
            "generation": 2,
            "position": 1,
            "pick": 1,
            "offer": ["phobos_space_haven", "space_mirrors", "media_archives", "business_network"],
            "picked": "phobos_space_haven",
            "drafted": [],
            "passed": [],
        },
        {
            "kind": "draft",
            "player": 0,
            "generation": 2,
            "position": 1,
            "pick": 2,
            "offer": ["space_mirrors", "media_archives", "business_network"],
            "picked": "space_mirrors",
            "drafted": ["electro_catapult"],
            "passed": [
                {"generation": 2, "cards": ["giant_ice_asteroid", "ice_cap_melting", "technology_demonstration"]}
            ],
        },
        {
            "kind": "draft",
            "player": 1,
            "generation": 2,
            "position": 1,
            "pick": 2,
            "offer": ["giant_ice_asteroid", "ice_cap_melting", "technology_demonstration"],
            "picked": "giant_ice_asteroid",
            "drafted": ["phobos_space_haven"],
            "passed": [{"generation": 2, "cards": ["space_mirrors", "media_archives", "business_network"]}],
        },
        {
            "kind": "draft",
            "player": 0,
            "generation": 2,
            "position": 1,
            "pick": 3,
            "offer": ["ice_cap_melting", "technology_demonstration"],
            "picked": "ice_cap_melting",
            "drafted": ["space_mirrors", "electro_catapult"],
            "passed": [
                {"generation": 2, "cards": ["giant_ice_asteroid", "ice_cap_melting", "technology_demonstration"]},
                {"generation": 2, "cards": ["media_archives", "business_network"]},
            ],
        },
        {
            "kind": "draft",
            "player": 1,
            "generation": 2,
            "position": 1,
            "pick": 3,
            "offer": ["media_archives", "business_network"],
            "picked": "media_archives",
            "drafted": ["phobos_space_haven", "giant_ice_asteroid"],
            "passed": [
                {"generation": 2, "cards": ["space_mirrors", "media_archives", "business_network"]},
                {"generation": 2, "cards": ["ice_cap_melting", "technology_demonstration"]},
            ],
        },
        {
            "kind": "buy",
            "player": 0,
            "generation": 2,
            "position": 1,
            "offer": ["space_mirrors", "electro_catapult", "business_network", "ice_cap_melting"],
            "picked": ["electro_catapult"],
            "passed": [
                {"generation": 2, "cards": ["giant_ice_asteroid", "ice_cap_melting", "technology_demonstration"]},
                {"generation": 2, "cards": ["media_archives", "business_network"]},
                {"generation": 2, "cards": ["technology_demonstration"]},
            ],
        },
        {
            "kind": "buy",
            "player": 1,
            "generation": 2,
            "position": 1,
            "offer": ["phobos_space_haven", "giant_ice_asteroid", "media_archives", "technology_demonstration"],
            "picked": ["phobos_space_haven"],
            "passed": [
                {"generation": 2, "cards": ["space_mirrors", "media_archives", "business_network"]},
                {"generation": 2, "cards": ["ice_cap_melting", "technology_demonstration"]},
                {"generation": 2, "cards": ["business_network"]},
            ],
        },
    ],
}

# Decisions of setup and the Research phase, which the records describe.
RECORDED_KINDS = {"corporation", "prelude_cards", "buy_cards", "draft"}
MAX_PICKS = 1_000


def engine_decisions() -> list[dict]:
    """The same Game in the engine: the recorded picks, then the first Prelude Card and Area offered, and a
    Pass in the Action phase. Each Decision of setup and the Research phase as its Player saw it."""
    game = tm_engine.Game(seed=7, players=2, prelude=True)
    picks = iter(recorded_decisions(GAME))
    seen = []
    for _ in range(MAX_PICKS):
        decision = game.decision
        view = game.player_view(decision["player"])
        if view["generation"] == 2 and view["phase"] == "action":
            return seen
        if decision["kind"] in RECORDED_KINDS:
            seen.append({"view": view, **decision})
            game.pick(next(picks)["picked"])
            continue
        types = [option["details"]["type"] for option in decision["options"]]
        game.pick(types.index("pass") if "pass" in types else 0)
    raise AssertionError(f"no Generation 2 Action phase after {MAX_PICKS} picks")


def test_the_records_give_the_decisions_the_engine_asks_with_the_same_options_and_picks():
    engine = engine_decisions()
    records = list(recorded_decisions(GAME))

    assert [(d["player"], d["kind"]) for d in records] == [(d["player"], d["kind"]) for d in engine]
    for record, asked in zip(records, engine, strict=True):
        assert [option["details"] for option in record["options"]] == [option["details"] for option in asked["options"]]
    # Setup: a Corporation, two Prelude Cards, two cards and done, for each Player; then three Draft picks
    # each, and in the Research phase a card and done each.
    assert len(records) == 2 * 6 + 2 * 3 + 2 * 2


# Fields that say what the view held, rather than what the position is.
WHAT_THE_VIEW_HELD = {"hand_known", "board_known"}
# Card and Option fields that the records may not know, and the field that says whether they do.
UNKNOWN_CARD_FIELDS = {
    "facts_known": ("price", "held_price", "tiles_short", "facts_known"),
    "card_resources_known": ("card_resources", "card_resources_known"),
}
UNKNOWN_OPTION_FIELDS = ("price", "facts_known")


def what_the_records_know(from_records: Encoding, from_engine: Encoding) -> tuple[list, list]:
    """Both Encodings cut to what the records know of the position: the global fields they don't mark missing,
    the cards outside the hand, and of card and Option rows the fields they know. The Area rows are left out,
    as the records give no Tiles after setup (`board_known`)."""
    cuts = []
    for encoding in (from_records, from_engine):
        known = [
            number
            for name, number, missing in zip(GLOBAL_FIELDS, encoding.globals, from_records.missing, strict=True)
            if not missing and name not in WHAT_THE_VIEW_HELD
        ]
        cards = [list(row) for row in encoding.cards if ZONES[int(row[1])] != "hand"]
        options = [list(row) for row in encoding.options]
        cuts.append((known, cards, options))
    (_, record_cards, record_options), (_, engine_cards, engine_options) = cuts
    for record_row, engine_row in zip(record_cards, engine_cards, strict=True):
        for flag, fields in UNKNOWN_CARD_FIELDS.items():
            if not record_row[CARD_FIELDS.index(flag)]:
                for field in fields:
                    engine_row[CARD_FIELDS.index(field)] = record_row[CARD_FIELDS.index(field)]
    for record_row, engine_row in zip(record_options, engine_options, strict=True):
        if not record_row[OPTION_FIELDS.index("facts_known")]:
            for field in UNKNOWN_OPTION_FIELDS:
                engine_row[OPTION_FIELDS.index(field)] = record_row[OPTION_FIELDS.index(field)]
    return cuts[0], cuts[1]


def test_a_position_in_the_records_and_the_same_position_in_the_engine_encode_alike():
    for record, asked in zip(recorded_decisions(GAME), engine_decisions(), strict=True):
        from_records = encode(record["view"], record)
        from_engine = encode(asked["view"], asked)

        # Everything the records know encodes as from the engine's full Player View...
        records_know, engine_shows = what_the_records_know(from_records, from_engine)
        assert records_know == engine_shows
        # ...and the engine's view cut to what the records give encodes exactly alike.
        assert from_records == encode(as_recorded(asked["view"]), asked)


def test_what_the_records_dont_hold_is_marked_missing_not_guessed():
    records = list(recorded_decisions(GAME))
    at_setup = encode(records[0]["view"], records[0])
    in_the_draft = encode(records[12]["view"], records[12])

    # At setup the board is empty and the hands too: unknown are who goes first, the decks' sizes, and the
    # Milestone and Award counts, which the records never give (they restate the Terraform Ratings, Tags and
    # Resources, which they do give).
    counts = [
        f"{kind}_{name}_{side}_count"
        for kind, names in (("milestone", MILESTONES), ("award", AWARDS))
        for name in names
        for side in ("my", "their")
    ]
    assert at_setup.missing_fields() == ["first_player_mine", "deck_size", "discard_size", "prelude_deck_size", *counts]
    # Later the records give neither the hands, nor the Tiles, nor Milestone and Award progress.
    missing = in_the_draft.missing_fields()
    assert {"my_hand_size", "their_hand_size", "my_tiles_city"} <= set(missing)
    assert {"milestone_mayor_my_count", "award_miner_their_count"} <= set(missing)
    assert in_the_draft.global_fields()["hand_known"] == 0
    assert in_the_draft.global_fields()["board_known"] == 0
    assert "my_resources_megacredits" not in missing
    # The Prices of Tags and cards read the hand and the Tiles, so they are unknown too, not priced as if the
    # hand and the board were empty.
    assert {f"price_tag_{tag}" for tag in TAGS} <= set(missing)
    assert "price_victory_point" not in missing
    offered = [in_the_draft.option(index) for index in range(len(in_the_draft.options))]
    assert [(option["price"], option["facts_known"]) for option in offered] == [(0, 0)] * len(offered)


# Random Games for the check below.
RANDOM_GAMES = 20


def test_nothing_the_records_lack_is_guessed_in_random_games():
    # Each setup, Draft and buy position of random Games, cut to what the records give: whatever the cut
    # encoding claims to know is what the full Player View encodes.
    checked = 0
    for seed in range(RANDOM_GAMES):
        game = tm_engine.Game(seed=seed, players=2, prelude=seed % 2 == 0)
        numbers = random.Random(seed)
        for _ in range(MAX_PICKS * 10):
            if game.is_over:
                break
            decision = game.decision
            if decision["kind"] in RECORDED_KINDS:
                view = game.player_view(decision["player"])
                records_know, engine_shows = what_the_records_know(
                    encode(as_recorded(view), decision), encode(view, decision)
                )
                assert records_know == engine_shows
                checked += 1
            game.pick(numbers.randrange(len(decision["options"])))

    assert checked > 1_000
