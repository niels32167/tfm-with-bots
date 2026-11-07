"""#P11 Excentric Sponsor (Prelude Card): play 1 card from hand with a 25 MegaCredit reduction. Playing it is
not optional; with no card in hand that could be played that way, Excentric Sponsor can't be played, and is
discarded for 15 MegaCredits."""

from tests.helpers import (
    card_costs,
    labels,
    pick,
    player,
    player_board,
    production,
    resources,
    scenario,
)


def test_excentric_sponsor_plays_a_card_for_25_megacredits_less():
    game = scenario(player(prelude_cards=["excentric_sponsor"], hand=["io_mining_industries", "mine"]), player(),
                    prelude=True)

    assert game.decision["kind"] == "play_card"
    assert labels(game) == ["Play Mine (0 MegaCredits)", "Play Io Mining Industries (16 MegaCredits)"]
    assert card_costs(game, 0) == {"io_mining_industries": 16, "mine": 0}
    pick(game, "Play Io Mining Industries")

    assert player_board(game, 0)["played_cards"] == ["io_mining_industries"]
    assert resources(game, 0)["megacredits"] == 42 - 16
    assert production(game, 0)["titanium"] == 2
    assert player_board(game, 0)["played_prelude_cards"] == ["excentric_sponsor"]


def test_a_card_costing_25_megacredits_or_less_is_free_and_with_none_left_over():
    game = scenario(player(prelude_cards=["excentric_sponsor"], hand=["mine"], megacredits=0), player(),
                    prelude=True)

    pick(game, "Play Mine")

    assert player_board(game, 0)["played_cards"] == ["mine"]
    assert resources(game, 0)["megacredits"] == 0


def test_only_the_card_it_plays_is_cheaper():
    game = scenario(player(prelude_cards=["excentric_sponsor"], hand=["mine", "io_mining_industries"]), player(),
                    prelude=True)

    pick(game, "Play Mine")

    assert card_costs(game, 0) == {"io_mining_industries": 41}


def test_with_no_card_it_could_play_it_cant_be_played_and_is_discarded_for_15_megacredits():
    requirement = scenario(player(prelude_cards=["excentric_sponsor"], hand=["trees"]), player(), prelude=True)
    too_dear = scenario(player(prelude_cards=["excentric_sponsor"], hand=["io_mining_industries"], megacredits=15),
                        player(), prelude=True)

    for game, megacredits in [(requirement, 57), (too_dear, 30)]:
        assert player_board(game, 0)["played_prelude_cards"] == []
        assert player_board(game, 0)["played_cards"] == []
        assert resources(game, 0)["megacredits"] == megacredits
