"""Valley Trust (Prelude's Corporation, Earth Tag): Effect: when you play a science Tag, you pay 2 MegaCredits less for
it. You start with 37 MegaCredits. As your first action, draw 3 Prelude cards, and play one of them. Discard the other
two."""

from tests.helpers import (
    PRELUDE_CARDS,
    card_costs,
    hand,
    labels,
    offered,
    pick,
    place_tiles_anywhere,
    player,
    player_board,
    prelude_cards,
    production,
    resources,
    scenario,
    start_as,
)

FIRST_ACTION = "First action of Valley Trust: draw 3 Prelude Cards and play one"


def valley_trust(**fields):
    return player(corporation="valley_trust", first_action_due=True, **fields)


def test_valley_trust_starts_with_37_megacredits_an_earth_tag_and_its_first_action_due():
    game, first = start_as("valley_trust", prelude=True)

    assert resources(game, first)["megacredits"] == 37
    assert player_board(game, first)["tags"]["earth"] == 1
    assert player_board(game, first)["first_action_due"] is True


def test_a_card_costs_2_megacredits_less_for_each_science_tag_on_it():
    game = scenario(player(corporation="valley_trust", hand=["research", "physics_complex", "mine"]), player(),
                    prelude=True)

    # Research has 2 science Tags, Physics Complex 1, Mine none.
    assert card_costs(game, 0) == {"research": 7, "physics_complex": 10, "mine": 4}


def test_its_first_action_draws_3_prelude_cards_and_plays_the_one_its_player_picks():
    game = scenario(valley_trust(), player(), prelude=True, prelude_deck=["donation", "loan", "supplier"])

    assert labels(game) == [FIRST_ACTION, "Pass"]
    pick(game, "First action")

    assert game.decision["kind"] == "play_prelude_card"
    assert labels(game) == ["Play Donation", "Play Loan", "Play Supplier"]
    assert prelude_cards(game, 0)["kept"] == ["donation", "loan", "supplier"]
    assert "Player 1 draws 3 Prelude Cards." in game.log
    pick(game, "Play Supplier")

    assert player_board(game, 0)["played_prelude_cards"] == ["supplier"]
    assert production(game, 0)["energy"] == 2
    assert resources(game, 0)["steel"] == 4
    assert prelude_cards(game, 0)["kept"] == []
    assert game.full_view()["prelude_deck_size"] == 0
    assert player_board(game, 0)["first_action_due"] is False
    assert game.full_view()["actions_this_turn"] == 1
    assert game.decision["kind"] == "action"


def test_the_prelude_cards_drawn_and_not_played_stay_hidden_from_the_others():
    game = scenario(valley_trust(), player(), prelude=True, prelude_deck=["donation", "loan", "supplier"])
    pick(game, "First action")

    assert game.player_view(1)["players"][0]["prelude_cards"] is None
    pick(game, "Play Donation")

    assert not any("Loan" in line or "Supplier" in line for line in game.log)
    assert game.player_view(1)["players"][0]["prelude_cards"] is None


def test_a_prelude_card_drawn_that_cant_be_played_is_discarded_for_15_megacredits_if_picked():
    game = scenario(valley_trust(megacredits=0, production={"megacredits": -4}), player(), prelude=True,
                    prelude_deck=["donation", "loan", "supplier"])
    pick(game, "First action")

    assert labels(game) == ["Play Donation", "Discard Loan for 15 MegaCredits (it can't be played)", "Play Supplier"]
    pick(game, "Discard Loan")

    assert resources(game, 0)["megacredits"] == 15
    assert game.full_view()["actions_this_turn"] == 1


def test_a_prelude_card_with_a_tile_ends_the_action_once_placed():
    game = scenario(valley_trust(), player(), prelude=True, prelude_deck=["early_settlement"])
    pick(game, "First action")

    # With one Prelude Card left in the deck, it is drawn alone, and still picked.
    assert labels(game) == ["Play Early Settlement"]
    pick(game, "Play Early Settlement")
    place_tiles_anywhere(game)

    assert production(game, 0)["plants"] == 1
    assert game.full_view()["actions_this_turn"] == 1


def test_a_prelude_card_that_plays_a_card_from_the_hand_ends_the_action_once_that_card_is_played():
    game = scenario(valley_trust(megacredits=13, hand=["trees"]), player(), prelude=True,
                    prelude_deck=["ecology_experts"])
    pick(game, "First action")
    pick(game, "Play Ecology Experts")

    # Trees needs -4 °C, which Ecology Experts ignores.
    pick(game, "Play Trees")

    assert hand(game, 0) == []
    assert game.full_view()["actions_this_turn"] == 1
    assert player_board(game, 0)["next_card"] is None


def test_a_prelude_card_with_a_price_ends_the_action_once_paid():
    game = scenario(valley_trust(megacredits=6), player(), prelude=True, prelude_deck=["business_empire"])
    pick(game, "First action")
    pick(game, "Play Business Empire")

    assert resources(game, 0)["megacredits"] == 0
    assert production(game, 0)["megacredits"] == 6
    assert game.full_view()["actions_this_turn"] == 1


def test_with_an_empty_prelude_deck_it_goes_without_its_first_action():
    game = scenario(valley_trust(), player(), prelude=True, prelude_deck=[])

    assert not offered(game, "First action")


def test_a_scenarios_prelude_deck_holds_every_prelude_card_it_names_nowhere_else():
    game = scenario(valley_trust(played_prelude_cards=["donation"]), player(prelude_cards=["loan"]), prelude=True)

    assert game.full_view()["prelude_deck_size"] == len(PRELUDE_CARDS) - 2
    assert game.to_scenario()["prelude_deck"] == sorted(
        (card for card in PRELUDE_CARDS if card not in ("donation", "loan")), key=PRELUDE_CARDS.index
    )


def test_in_a_new_game_the_prelude_deck_holds_the_prelude_cards_not_dealt():
    game, _ = start_as("valley_trust", prelude=True, players=3)

    assert game.full_view()["prelude_deck_size"] == len(PRELUDE_CARDS) - 3 * 4


def test_a_game_described_as_a_scenario_while_its_player_chooses_starts_before_the_first_action():
    game = scenario(valley_trust(), player(), prelude=True, prelude_deck=["donation", "loan", "supplier"])
    pick(game, "First action")

    described = game.to_scenario()

    assert described["players"][0]["first_action_due"] is True
    assert described["players"][0].get("prelude_cards", []) == []
    assert described["prelude_deck"] == ["donation", "loan", "supplier"]
    assert labels(scenario(*described["players"], **{k: v for k, v in described.items() if k != "players"})) == [
        FIRST_ACTION,
        "Pass",
    ]
