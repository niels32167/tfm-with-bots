"""Importing one Recorded Game: its settings and results, and each Draft and buy Decision as the Player
who made it saw it."""

import json

import pytest

from ai.recorded_games.importer import Skipped, import_game
from tests.ai.recorded_games.logs import ADA, BO, SALT, decisions, prelude_log


def test_settings_and_results_are_kept_with_anonymous_players():
    game = import_game(prelude_log(), SALT)

    assert game["date"] == "2025-02-02"
    assert game["prelude"] is True
    assert game["conceded"] is False
    assert game["generations"] == 2
    assert game["scraper_version"] == "v2025.10.07.1844"
    ada, bo = game["players"]
    assert (ada["rating"], ada["rating_change"], ada["corporation"], ada["victory_points"], ada["winner"]) == (
        612,
        9,
        "teractor",
        61,
        True,
    )
    assert (bo["rating"], bo["corporation"], bo["victory_points"], bo["winner"]) == (540, "tharsis_republic", 48, False)
    assert bo["points"] == {"tr": 28, "awards": 5, "milestones": 5, "cities": 3, "greeneries": 5, "cards": 3}


def test_no_name_or_board_game_arena_id_is_kept():
    game = import_game(prelude_log(), SALT)

    text = json.dumps(game)
    for leak in ("Ada", 'Bo"', ADA, BO, "624518601"):
        assert leak not in text
    ada, bo = game["players"]
    assert ada["id"] != bo["id"]
    # The same salt gives the same anonymous ids, so a Player can be followed across Games.
    assert import_game(prelude_log(), SALT)["players"][0]["id"] == ada["id"]
    assert import_game(prelude_log(), b"another salt")["players"][0]["id"] != ada["id"]


def with_changes(**changes):
    log = prelude_log()
    log.update(changes)
    return log


@pytest.mark.parametrize(
    ("changes", "reason"),
    [
        ({"map": "Hellas"}, "map Hellas"),
        ({"colonies_on": True}, "Colonies"),
        ({"draft_on": False}, "no Draft"),
        ({"corporate_era_on": False}, "no Corporate Era"),
        ({"beginners_corporations_on": True}, "Beginner Corporations"),
    ],
)
def test_games_of_other_kinds_are_skipped_with_the_reason(changes, reason):
    with pytest.raises(Skipped) as skipped:
        import_game(with_changes(**changes), SALT)

    assert skipped.value.reason == reason


def test_games_with_other_player_counts_are_skipped():
    log = prelude_log()
    log["players"]["3003"] = dict(log["players"][BO], player_id="3003", player_name="Cy")

    with pytest.raises(Skipped) as skipped:
        import_game(log, SALT)

    assert skipped.value.reason == "3 Players"


def test_games_without_prelude_are_kept_and_marked():
    assert import_game(with_changes(prelude_on=False), SALT)["prelude"] is False


def test_each_player_s_setup_holds_what_they_were_dealt_and_what_they_kept():
    game = import_game(prelude_log(), SALT)

    [ada_setup] = decisions(game, "setup", 0)
    assert ada_setup["generation"] == 1
    assert ada_setup["offer"] == {
        "corporations": ["teractor", "mining_guild"],
        "prelude_cards": ["biofuels", "excentric_sponsor", "io_research_outpost", "metal_rich_asteroid"],
        "cards": [
            "business_contacts", "solar_power", "hackers", "decomposers", "fusion_power",
            "cartel", "predators", "interstellar_colony_ship", "towing_a_comet", "grass",
        ],
    }  # fmt: skip
    assert ada_setup["picked"] == {
        "corporation": "teractor",
        "prelude_cards": ["excentric_sponsor", "metal_rich_asteroid"],
        "cards": ["business_contacts", "solar_power", "decomposers", "cartel"],
    }
    [bo_setup] = decisions(game, "setup", 1)
    assert bo_setup["picked"] == {
        "corporation": "tharsis_republic",
        "prelude_cards": ["galilean_mining", "orbital_construction_yard"],
        "cards": ["methane_from_titan", "imported_hydrogen"],
    }


def test_each_draft_pick_holds_the_hand_on_offer_the_cards_drafted_so_far_and_those_passed_on():
    game = import_game(prelude_log(), SALT)

    ada = [(d["generation"], d["pick"], d["offer"], d["picked"], d["drafted"]) for d in decisions(game, "draft", 0)]
    assert ada == [
        (
            2,
            1,
            ["kelp_farming", "standard_technology", "terraforming_ganymede", "olympus_conference"],
            "kelp_farming",
            [],
        ),
        (2, 2, ["big_asteroid", "deimos_down", "tundra_farming"], "deimos_down", ["kelp_farming"]),
        (
            2,
            3,
            ["standard_technology", "terraforming_ganymede"],
            "standard_technology",
            ["kelp_farming", "deimos_down"],
        ),
    ]  # The last card is no Decision: it comes by itself.
    first, second, third = decisions(game, "draft", 0)
    assert first["passed"] == []
    assert second["passed"] == [
        {"generation": 2, "cards": ["standard_technology", "terraforming_ganymede", "olympus_conference"]}
    ]
    assert third["passed"] == [
        {"generation": 2, "cards": ["standard_technology", "terraforming_ganymede", "olympus_conference"]},
        {"generation": 2, "cards": ["big_asteroid", "tundra_farming"]},
    ]
    bo = [(d["pick"], d["offer"], d["picked"]) for d in decisions(game, "draft", 1)]
    assert bo == [
        (1, ["industrial_microbes", "big_asteroid", "deimos_down", "tundra_farming"], "industrial_microbes"),
        (2, ["standard_technology", "terraforming_ganymede", "olympus_conference"], "olympus_conference"),
        (3, ["big_asteroid", "tundra_farming"], "big_asteroid"),
    ]


def test_each_buy_offers_the_cards_drafted_and_holds_those_kept():
    game = import_game(prelude_log(), SALT)

    [ada] = decisions(game, "buy", 0)
    assert (ada["generation"], ada["offer"], ada["picked"]) == (
        2,
        ["kelp_farming", "deimos_down", "standard_technology", "tundra_farming"],
        ["kelp_farming", "deimos_down"],
    )
    assert ada["passed"] == [
        {"generation": 2, "cards": ["standard_technology", "terraforming_ganymede", "olympus_conference"]},
        {"generation": 2, "cards": ["big_asteroid", "tundra_farming"]},
        {"generation": 2, "cards": ["terraforming_ganymede"]},
    ]
    [bo] = decisions(game, "buy", 1)
    assert (bo["offer"], bo["picked"]) == (
        ["industrial_microbes", "olympus_conference", "big_asteroid", "terraforming_ganymede"],
        ["industrial_microbes", "olympus_conference", "big_asteroid"],
    )


def test_decisions_come_in_the_order_they_were_made():
    game = import_game(prelude_log(), SALT)

    # Both Players pick at the same time in each round of the Draft: by their place within it.
    order = [(d["kind"], d["player"], d.get("pick")) for d in game["decisions"]]
    assert order == [
        ("setup", 0, None), ("setup", 1, None),
        ("draft", 0, 1), ("draft", 1, 1), ("draft", 0, 2), ("draft", 1, 2), ("draft", 0, 3), ("draft", 1, 3),
        ("buy", 1, None), ("buy", 0, None),
    ]  # fmt: skip


def position_of(game, decision):
    return game["positions"][decision["position"]]


def test_setup_decisions_see_the_starting_position():
    game = import_game(prelude_log(), SALT)

    [ada_setup] = decisions(game, "setup", 0)
    state = position_of(game, ada_setup)
    assert (state["generation"], state["temperature"], state["oxygen"], state["oceans"]) == (1, -30, 0, 0)
    assert [player["corporation"] for player in state["players"]] == [None, None]
    assert [player["played"] for player in state["players"]] == [[], []]


def test_research_decisions_see_the_public_position_after_production():
    game = import_game(prelude_log(), SALT)

    [ada_buy] = decisions(game, "buy", 0)
    state = position_of(game, ada_buy)
    assert all(
        decision["position"] == ada_buy["position"] for decision in game["decisions"] if decision["generation"] == 2
    )
    assert (state["generation"], state["temperature"]) == (2, -28)
    ada, bo = state["players"]
    # Ada ended Generation 1 with 5 MegaCredits, 2 energy and 1 heat, a Terraform Rating of 21, and
    # Production of 3 MegaCredits, 1 energy and 2 heat. Energy turns into heat, then Production comes in.
    assert ada["resources"] == {"megacredits": 29, "steel": 0, "titanium": 0, "plants": 0, "energy": 1, "heat": 5}
    assert ada["production"] == {"megacredits": 3, "steel": 0, "titanium": 0, "plants": 0, "energy": 1, "heat": 2}
    assert bo["resources"] == {"megacredits": 36, "steel": 4, "titanium": 0, "plants": 3, "energy": 0, "heat": 0}
    assert (ada["terraform_rating"], bo["terraform_rating"]) == (21, 20)
    assert ada["tags"]["earth"] == 1
    assert (ada["hand_counter"], bo["hand_counter"]) == (3, 2)
    assert (ada["corporation"], bo["corporation"]) == ("teractor", "tharsis_republic")
    # Deimos Down is played after the Research phase.
    assert (ada["played"], ada["prelude_cards"]) == (["solar_power"], ["excentric_sponsor"])
    assert (bo["played"], bo["prelude_cards"]) == ([], ["galilean_mining"])


def test_research_decisions_see_milestones_and_awards_claimed_and_funded_before():
    log = prelude_log()
    for entry in log["moves"][7:10]:
        entry["game_state"]["milestones"] = {"Builder": {"claimed_by": "Bo", "player_id": BO, "move_number": 8}}
        entry["game_state"]["awards"] = {"Bankier": {"funded_by": "Ada", "player_id": ADA, "move_number": 8}}
    game = import_game(log, SALT)

    [ada_buy] = decisions(game, "buy", 0)
    state = position_of(game, ada_buy)
    assert (state["milestones"], state["awards"]) == ({"builder": 1}, {"banker": 0})


def card_ids_in(value):
    """Every string anywhere in a record."""
    if isinstance(value, str):
        return {value}
    if isinstance(value, dict):
        return set().union(*(card_ids_in(item) for item in value.values())) if value else set()
    if isinstance(value, list):
        return set().union(*(card_ids_in(item) for item in value)) if value else set()
    return set()


def seen_by(game, player):
    """All that a Player's Decisions show them: the records and the public positions they point to."""
    return set().union(
        *(card_ids_in(d) | card_ids_in(position_of(game, d)) for d in game["decisions"] if d["player"] == player)
    )


def test_no_record_holds_cards_hidden_from_its_player():
    game = import_game(prelude_log(), SALT)

    # Bo's dealt cards he didn't play, and Industrial Microbes, which he took from his first Draft hand
    # before Ada saw it; Ada saw the rest of that hand, as he passed it to her.
    hidden_from_ada = {
        "robinson_industries", "power_generation", "supply_drop", "methane_from_titan", "imported_hydrogen",
        "eos_chasma_national_park", "deep_well_heating", "optimal_aerobraking", "cloud_seeding",
        "great_escarpment_consortium", "lava_flows", "mangrove", "moss", "industrial_microbes", "orbital_construction_yard",
    }  # fmt: skip
    hidden_from_bo = {
        "mining_guild", "biofuels", "io_research_outpost", "metal_rich_asteroid", "business_contacts", "hackers",
        "decomposers", "fusion_power", "cartel", "predators", "interstellar_colony_ship", "towing_a_comet", "grass",
        "lichen", "kelp_farming",
    }  # fmt: skip
    assert seen_by(game, 0) & hidden_from_ada == set()
    assert seen_by(game, 1) & hidden_from_bo == set()
    # Played cards are public, and cards passed on stay known to who passed them.
    assert {"galilean_mining", "big_asteroid", "deimos_down", "tundra_farming"} <= seen_by(game, 0)
    assert {"excentric_sponsor", "solar_power", "standard_technology", "terraforming_ganymede"} <= seen_by(game, 1)


def test_results_hold_the_milestones_claimed_and_awards_funded_with_their_generation():
    log = prelude_log()
    log["moves"][-1]["game_state"]["milestones"]["Builder"] = {"claimed_by": "Bo", "player_id": BO, "move_number": 5}

    game = import_game(log, SALT)
    assert game["milestones"] == [
        {"milestone": "builder", "player": 1, "generation": 1},
        {"milestone": "planner", "player": 0, "generation": 2},
    ]
    assert game["awards"] == [{"award": "thermalist", "player": 1, "generation": 2}]


def test_a_game_without_a_named_winner_or_places_has_none():
    log = prelude_log()
    del log["winner"]
    for player in log["players"].values():
        del player["player_name"]
        del player["elo_data"]["position"]

    assert [player["winner"] for player in import_game(log, SALT)["players"]] == [False, False]
