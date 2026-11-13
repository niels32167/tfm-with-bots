"""Hand-written Recorded Game logs in the scraper's JSON shape, for the importer's tests.

The Game: Ada and Bo, 2 Players on Tharsis with Prelude and the Draft, from Ada's perspective. Ada
chooses Teractor and Bo Tharsis Republic; in Generation 2 they draft 4 cards each and buy some. Real logs
name both Players' cards, as these do.
"""

import copy
from typing import Any

ADA, BO = "1001", "2002"

# The tests' salt for anonymous ids.
SALT = b"test salt"
NAMES = {ADA: "Ada", BO: "Bo"}

ADA_DEALT = {
    "corporations": ["Teractor", "Mining Guild"],
    "preludes": ["Biofuels", "Excentric Sponsor", "Io Research Outpost", "Metal-Rich Asteroid"],
    "project_cards": [
        "Business Contacts", "Solar Power", "Hackers", "Decomposers", "Fusion Power",
        "Cartel", "Predators", "Interstellar Colony Ship", "Towing a Comet", "Grass",
    ],
}  # fmt: skip
BO_DEALT = {
    "corporations": ["Tharsis Republic", "Robinson Industries"],
    "preludes": ["Galilean Mining", "Orbital Construction Yard", "Power Generation", "Supply Drop"],
    "project_cards": [
        "Methane From Titan", "Imported Hydrogen", "Eos Chasma National Park", "Deep Well Heating",
        "Optimal Aerobraking", "Cloud Seeding", "Great Escarpment Consortium", "Lava Flows", "Mangrove", "Moss",
    ],
}  # fmt: skip
ADA_KEPT = [
    "Teractor",
    "Business Contacts",
    "Solar Power",
    "Decomposers",
    "Cartel",
    "Excentric Sponsor",
    "Metal-Rich Asteroid",
]
BO_KEPT = [
    "Tharsis Republic",
    "Methane From Titan",
    "Imported Hydrogen",
    "Galilean Mining",
    "Orbital Construction Yard",
]

# Generation 2's Draft: each is dealt 4, keeps 1 and passes the rest to the other, until all are picked.
ADA_FIRST_DRAFT_HAND = ["Kelp Farming", "Standard Technology", "Terraforming Ganymede", "Olympus Conference"]
BO_FIRST_DRAFT_HAND = ["Industrial Microbes", "Big Asteroid", "Deimos Down", "Tundra Farming"]

TRACKER_NAMES = [
    "M€", "M€ Production", "Steel", "Steel Production", "Titanium", "Titanium Production", "Plant",
    "Plant Production", "Energy", "Energy Production", "Heat", "Heat Production", "Count of Building tags",
    "Count of Space tags", "Count of Science tags", "Count of Power tags", "Count of Earth tags",
    "Count of Jovian tags", "Count of Plant tags", "Count of Microbe tags", "Count of Animal tags",
    "Count of City tags", "Count of Wild tags", "Count of played Events cards", "Hand Counter",
    "Player Area Counter", "Microbe",
]  # fmt: skip


def trackers(**values: int) -> dict[str, int]:
    """A Player's trackers, 0 except as given: m=M€, m_production, steel, heat, energy_production..."""
    names = {
        "m": "M€", "m_production": "M€ Production", "steel": "Steel", "steel_production": "Steel Production",
        "plants": "Plant", "plant_production": "Plant Production", "energy": "Energy",
        "energy_production": "Energy Production", "heat": "Heat", "heat_production": "Heat Production",
        "earth_tags": "Count of Earth tags", "space_tags": "Count of Space tags", "hand": "Hand Counter",
        "events": "Count of played Events cards",
    }  # fmt: skip
    counters = dict.fromkeys(TRACKER_NAMES, 0)
    for key, value in values.items():
        counters[names[key]] = value
    return counters


def game_state(
    generation: int,
    ada: dict[str, int],
    bo: dict[str, int],
    tr: tuple[int, int] = (20, 20),
    temperature: int = -30,
    milestones: dict[str, Any] | None = None,
    awards: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "move_number": 0,
        "generation": generation,
        "temperature": temperature,
        "oxygen": 0,
        "oceans": 0,
        "player_vp": {
            pid: {
                "total": rating,
                "total_details": {"tr": rating, "awards": 0, "milestones": 0, "cities": 0, "greeneries": 0, "cards": 0},
            }
            for pid, rating in zip((ADA, BO), tr)
        },
        "milestones": milestones or {},
        "awards": awards or {},
        "player_trackers": {ADA: ada, BO: bo},
    }


def move(
    number: int, who: str, action_type: str, description: str, state: dict[str, Any], **fields: Any
) -> dict[str, Any]:
    entry = {
        "move_number": number,
        "timestamp": "7:20:55",
        "player_id": who,
        "player_name": NAMES[who],
        "action_type": action_type,
        "description": description,
        "card_played": None,
        "card_drafted": None,
        "tile_placed": None,
        "tile_location": None,
        "card_options": None,
        "cards_kept": None,
        "reason": None,
        "game_state": copy.deepcopy(state),
    }
    entry.update(fields)
    return entry


def keeps(name: str, cards: list[str]) -> str:
    return f"{name} keeps {len(cards)} cards: {', '.join(cards)}"


def prelude_log() -> dict[str, Any]:
    """The whole Game: setup, a short Generation 1, Generation 2's Draft and buy, and a play."""
    start = game_state(1, trackers(), trackers())
    after_setup = game_state(1, trackers(m=33, hand=4, m_production=1), trackers(m=40, hand=2, m_production=2, steel=4))
    end_of_1 = game_state(
        1,
        trackers(m=5, m_production=3, energy=2, energy_production=1, heat=1, heat_production=2, hand=3, earth_tags=1),
        trackers(m=12, m_production=4, plants=2, plant_production=1, steel=4, hand=2),
        tr=(21, 20),
        temperature=-28,
    )
    gen_2 = copy.deepcopy(end_of_1)
    gen_2["generation"] = 2
    moves = [
        move(
            1, ADA, "other", "The color of Ada has been chosen according to their preferences. | Ada is starting player for this generation", start,
            card_options={ADA: ADA_DEALT["project_cards"], BO: BO_DEALT["project_cards"]},
        ),
        move(2, BO, "draft", keeps("Bo", BO_KEPT), start, card_drafted="Orbital Construction Yard", cards_kept={BO: BO_KEPT}, reason="draft"),
        move(
            3, ADA, "other", f"{keeps('Ada', ADA_KEPT)} | {keeps('Bo', BO_KEPT)} | Ada pays 12 M€", after_setup,
            card_drafted="Teractor", cards_kept={ADA: ADA_KEPT, BO: BO_KEPT},
        ),
        move(4, ADA, "play_card", "Ada plays card Excentric Sponsor", after_setup, card_played="Excentric Sponsor"),
        move(5, BO, "play_card", "Bo plays card Galilean Mining | Bo increases Titanium Production by 1", after_setup, card_played="Galilean Mining"),
        move(6, ADA, "play_card", "Ada pays 11 M€ | Ada plays card Solar Power", after_setup, card_played="Solar Power"),
        move(7, ADA, "draw", "Ada draws 1 cards: Lichen", after_setup, cards_kept={ADA: ["Lichen"]}),
        move(8, BO, "pass", "Bo passes | Bo pass", end_of_1),
        move(9, ADA, "pass", "Ada passes", end_of_1),
        move(
            10, ADA, "pass",
            f"Ada drafts 4 cards: {', '.join(ADA_FIRST_DRAFT_HAND)} | Bo drafts 4 cards: {', '.join(BO_FIRST_DRAFT_HAND)} | Ada gains 24 M€",
            gen_2, card_options={ADA: ADA_FIRST_DRAFT_HAND, BO: BO_FIRST_DRAFT_HAND},
        ),
        move(11, ADA, "draft", "You draft Kelp Farming", gen_2, card_drafted="Kelp Farming", reason="draft"),
        move(
            12, BO, "draft", "Bo drafts Industrial Microbes", gen_2, card_drafted="Industrial Microbes", reason="draft",
            card_options={ADA: ["Big Asteroid", "Deimos Down", "Tundra Farming"], BO: ["Standard Technology", "Terraforming Ganymede", "Olympus Conference"]},
        ),
        move(13, BO, "draft", "You draft Olympus Conference", gen_2, card_drafted="Olympus Conference", reason="draft"),
        move(
            14, ADA, "draft", "You draft Deimos Down", gen_2, card_drafted="Deimos Down", reason="draft",
            card_options={ADA: ["Standard Technology", "Terraforming Ganymede"], BO: ["Big Asteroid", "Tundra Farming"]},
        ),
        move(15, BO, "draft", "You draft Big Asteroid", gen_2, card_drafted="Big Asteroid", reason="draft"),
        move(
            16, ADA, "draft", "You draft Standard Technology", gen_2, card_drafted="Standard Technology", reason="draft",
            card_options={ADA: ["Tundra Farming"], BO: ["Terraforming Ganymede"]},
        ),
        move(17, BO, "draft", "You draft Terraforming Ganymede", gen_2, card_drafted="Terraforming Ganymede", reason="draft"),
        move(18, ADA, "draft", "You draft Tundra Farming", gen_2, card_drafted="Tundra Farming", reason="draft"),
        move(
            19, BO, "buy_card", f"{keeps('Bo', ['Industrial Microbes', 'Olympus Conference', 'Big Asteroid'])} | Bo pays 9 M€", gen_2,
            card_drafted="Industrial Microbes", cards_kept={BO: ["Industrial Microbes", "Olympus Conference", "Big Asteroid"]},
        ),
        move(
            20, ADA, "buy_card", f"{keeps('Ada', ['Kelp Farming', 'Deimos Down'])} | Ada pays 6 M€", gen_2,
            card_drafted="Kelp Farming", cards_kept={ADA: ["Kelp Farming", "Deimos Down"], BO: ["Big Asteroid", "Industrial Microbes", "Olympus Conference"]},
        ),
        move(21, ADA, "play_card", "Ada pays 13 M€ | Ada plays card Deimos Down", gen_2, card_played="Deimos Down"),
        move(22, BO, "play_card", "Bo plays card Big Asteroid", gen_2, card_played="Big Asteroid"),
    ]  # fmt: skip
    final = game_state(
        2, trackers(), trackers(), tr=(30, 27),
        milestones={"Planner": {"claimed_by": "Ada", "player_id": ADA, "move_number": 21, "timestamp": "7:36:01"}},
        awards={"Thermalist": {"funded_by": "Bo", "player_id": BO, "move_number": 22, "timestamp": "7:49:00"}},
    )  # fmt: skip
    moves[-1]["game_state"] = final
    return {
        "replay_id": "624518601",
        "player_perspective": ADA,
        "game_date": "2025-02-02",
        "game_duration": "01:09",
        "winner": "Ada",
        "generations": 2,
        "conceded": False,
        "map": "Tharsis",
        "prelude_on": True,
        "colonies_on": False,
        "corporate_era_on": True,
        "draft_on": True,
        "beginners_corporations_on": False,
        "game_speed": "Real-time • Fast paced",
        "players": {
            ADA: player(ADA, "Teractor", 61, ADA_DEALT, ["Excentric Sponsor", "Solar Power", "Deimos Down"], rank=612, change=9, position=1),
            BO: player(BO, "Tharsis Republic", 48, BO_DEALT, ["Galilean Mining", "Big Asteroid"], rank=540, change=-9, position=2),
        },
        "moves": moves,
        "metadata": {"parsed_at": "2025-08-22T22:29:45", "total_moves": len(moves), "scraper_version": "v2025.10.07.1844"},
        "table_id": "624518601",
    }  # fmt: skip


def player(
    pid: str,
    corporation: str,
    points: int,
    dealt: dict[str, list[str]],
    played: list[str],
    *,
    rank: int,
    change: int,
    position: int,
) -> dict[str, Any]:
    return {
        "player_id": pid,
        "player_name": NAMES[pid],
        "corporation": corporation,
        "final_vp": points,
        "final_tr": points - 20,
        "vp_breakdown": {"tr": points - 20, "awards": 5, "milestones": 5, "cities": 3, "greeneries": 5, "cards": 3},
        "milestones_claimed": ["Planner"] if pid == ADA else [],
        "awards_funded": [] if pid == ADA else ["Thermalist"],
        "starting_hand": copy.deepcopy(dealt),
        "cards_played": played,
        "elo_data": {
            "arena_points": None, "arena_points_change": None, "game_rank": rank, "game_rank_change": change,
            "player_name": NAMES[pid], "player_id": pid, "position": position,
        },
    }  # fmt: skip


def decisions(game: dict[str, Any], kind: str, player: int) -> list[dict[str, Any]]:
    """A Player's Decisions of one kind in an imported Game, in order."""
    return [decision for decision in game["decisions"] if decision["kind"] == kind and decision["player"] == player]
