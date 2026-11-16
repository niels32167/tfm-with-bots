"""A chosen deal: a new Game whose first player and cards come in a given order instead of shuffled, so
that a Recorded Game can be replayed through the engine (ticket 10 of phase 2). Cards the deal leaves out
are shuffled beneath those it names. The deal is part of the settings, so the Replay reproduces the Game
(ADR 0010)."""

import pytest
import tm_engine

from tests.helpers import (
    MAX_PICKS,
    end_the_action_phase,
    everything_about,
    pick,
    play_randomly,
    player_board,
)

CORPORATIONS = ["mining_guild", "ecoline", "teractor", "valley_trust"]
DEALT_PRELUDE_CARDS = [
    "donation", "nitrogen_shipment", "power_generation", "research_network",
    "early_settlement", "excentric_sponsor", "io_research_outpost", "smelting_plant",
]  # fmt: skip
SETUP_CARDS = [
    "business_network", "dust_seals", "soil_factory", "immigration_shuttles", "restricted_area",
    "nuclear_power", "lightning_harvest", "fish", "quantum_extractor", "callisto_penal_mines",
    "media_group", "artificial_photosynthesis", "power_plant", "adaptation_technology", "standard_technology",
    "nitrite_reducing_bacteria", "special_design", "predators", "mining_expedition", "psychrophiles",
]  # fmt: skip
DRAFT_HANDS = [
    "industrial_center", "mars_university", "great_dam", "water_import_from_europa",
    "release_of_inert_gases", "small_animals", "noctis_city", "research_coordination",
]  # fmt: skip


def dealt_game(first_player: int = 1, **deal: list[str]) -> tm_engine.Game:
    cards = {"corporations": CORPORATIONS, "prelude_cards": DEALT_PRELUDE_CARDS, "project_cards": SETUP_CARDS}
    return tm_engine.Game(seed=5, prelude=True, deal={"first_player": first_player, **cards, **deal})


def test_setup_deals_the_corporations_prelude_cards_and_cards_in_the_order_given_from_the_first_player():
    game = dealt_game(first_player=1)

    assert game.full_view()["first_player"] == 1
    second, first = player_board(game, 0), player_board(game, 1)
    assert sorted(first["choosing_corporation"]["dealt"]) == ["ecoline", "mining_guild"]
    assert sorted(second["choosing_corporation"]["dealt"]) == ["teractor", "valley_trust"]
    assert sorted(first["prelude_cards"]["dealt"]) == sorted(DEALT_PRELUDE_CARDS[:4])
    assert sorted(second["prelude_cards"]["dealt"]) == sorted(DEALT_PRELUDE_CARDS[4:])
    assert sorted(first["buying"]["dealt"]) == sorted(SETUP_CARDS[:10])
    assert sorted(second["buying"]["dealt"]) == sorted(SETUP_CARDS[10:])


def test_later_draws_come_in_the_order_given_and_the_rest_of_the_deck_is_shuffled_beneath():
    game = dealt_game(project_cards=SETUP_CARDS + DRAFT_HANDS)

    deck = game.full_view()["deck"]
    assert deck[: len(DRAFT_HANDS)] == DRAFT_HANDS
    assert len(set(deck)) == len(deck)
    assert not set(deck) & set(SETUP_CARDS)


def test_the_draft_hands_of_generation_2_are_the_next_cards_in_player_order_from_its_first_player():
    game = dealt_game(first_player=1, project_cards=SETUP_CARDS + DRAFT_HANDS)
    end_the_setup_and_generation_1(game)

    assert game.decision["kind"] == "draft"
    assert game.full_view()["first_player"] == 0
    assert sorted(player_board(game, 0)["drafting"]["picking_from"]) == sorted(DRAFT_HANDS[:4])
    assert sorted(player_board(game, 1)["drafting"]["picking_from"]) == sorted(DRAFT_HANDS[4:])


def test_valley_trusts_first_action_draws_the_next_prelude_cards_given():
    shown = ["supplier", "loan", "biofuels"]
    game = dealt_game(first_player=0, prelude_cards=DEALT_PRELUDE_CARDS + shown)
    pick(game, type="choose_corporation", card="mining_guild")
    keep_and_buy_nothing(game)
    pick(game, type="choose_corporation", card="valley_trust")
    keep_and_buy_nothing(game)
    play_prelude_cards(game)
    pick(game, "Pass")

    pick(game, "First action")

    assert sorted(player_board(game, 1)["prelude_cards"]["kept"]) == sorted(shown)


def test_a_dealt_game_is_saved_with_its_deal_and_comes_back_from_its_replay():
    game = dealt_game(project_cards=SETUP_CARDS + DRAFT_HANDS)
    play_randomly(game, seed=3, picks=300)

    assert game.replay["start"]["settings"]["deal"]["project_cards"] == SETUP_CARDS + DRAFT_HANDS
    assert everything_about(tm_engine.Game.from_replay(game.replay)) == everything_about(game)


def test_a_game_without_a_deal_saves_no_deal():
    assert "deal" not in tm_engine.Game(seed=5, prelude=True).replay["start"]["settings"]


@pytest.mark.parametrize(
    ("deal", "error"),
    [
        ({"project_cards": ["mine", "mine"]}, "'mine' can be dealt only once"),
        ({"project_cards": ["no_such_card"]}, "there is no Project Card 'no_such_card'"),
        ({"corporations": ["mine"]}, "there is no Corporation 'mine'"),
        ({"prelude_cards": ["mine"]}, "there is no Prelude Card 'mine'"),
        ({"first_player": 2}, "the first player must be one of the Players, indexed 0 to 1, not 2"),
    ],
)
def test_a_deal_naming_a_card_that_cant_be_dealt_is_refused(deal, error):
    with pytest.raises(ValueError, match=error):
        tm_engine.Game(seed=5, prelude=True, deal=deal)


def test_a_deal_without_prelude_names_no_prelude_card():
    with pytest.raises(ValueError, match="there is no Prelude Card 'donation'"):
        tm_engine.Game(seed=5, deal={"prelude_cards": ["donation"]})


def keep_and_buy_nothing(game: tm_engine.Game) -> None:
    """The Player deciding keeps the first 2 Prelude Cards offered and buys no cards."""
    game.pick(0)
    game.pick(0)
    pick(game, "Done")


def play_prelude_cards(game: tm_engine.Game) -> None:
    """Both Players play their Prelude Cards, taking the first Option at each Decision, until a Turn begins."""
    for _ in range(MAX_PICKS):
        if game.decision["kind"] == "action":
            return
        game.pick(0)
    raise AssertionError(f"Prelude Cards were still being played after {MAX_PICKS} picks")


def end_the_setup_and_generation_1(game: tm_engine.Game) -> None:
    for _ in range(2):
        pick(game, type="choose_corporation", card=game.decision["options"][0]["details"]["card"])
        keep_and_buy_nothing(game)
    play_prelude_cards(game)
    end_the_action_phase(game)
