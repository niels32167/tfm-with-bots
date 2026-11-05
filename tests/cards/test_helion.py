"""Helion (space Tag): Effect: you may use heat as MegaCredits. You may not use MegaCredits as heat.
You start with 3 heat Production and 42 MegaCredits."""

from tests.helpers import (
    NO_INCOME,
    buy,
    end_the_action_phase,
    hand,
    labels,
    offered,
    options,
    pick,
    player,
    player_board,
    production,
    resources,
    scenario,
    skip_buying,
    start_as,
)


def ways_to_pay(game):
    """Each way to pay the Decision offers, as (MegaCredits, steel, titanium, heat)."""
    return [
        tuple(
            option["details"][part]
            for part in ("megacredits", "steel", "titanium", "heat")
        )
        for option in options(game)
    ]


def test_helion_starts_with_3_heat_production_42_megacredits_and_a_space_tag():
    game, first = start_as("helion")

    assert resources(game, first) == {
        "megacredits": 42,
        "steel": 0,
        "titanium": 0,
        "plants": 0,
        "energy": 0,
        "heat": 0,
    }
    assert production(game, first) == {
        "megacredits": 0,
        "steel": 0,
        "titanium": 0,
        "plants": 0,
        "energy": 0,
        "heat": 3,
    }
    assert player_board(game, first)["tags"]["space"] == 1


def test_heat_may_pay_for_a_card_in_any_split_with_megacredits():
    game = scenario(
        player(corporation="helion", megacredits=2, heat=5, hand=["sponsors"]), player()
    )

    pick(game, "Play Sponsors")

    assert game.decision["kind"] == "payment"
    assert ways_to_pay(game) == [(2, 0, 0, 4), (1, 0, 0, 5)]
    pick(game, type="payment", heat=4)
    assert resources(game, 0)["megacredits"] == 0
    assert resources(game, 0)["heat"] == 1
    assert "Player 1 plays Sponsors, paying 2 MegaCredits and 4 heat." in game.log


def test_with_only_heat_to_pay_with_there_is_nothing_to_choose():
    game = scenario(
        player(corporation="helion", megacredits=0, heat=6, hand=["sponsors"]), player()
    )

    pick(game, "Play Sponsors")

    assert resources(game, 0)["heat"] == 0
    assert player_board(game, 0)["played_cards"] == ["sponsors"]


def test_a_card_it_can_pay_for_only_with_heat_is_offered():
    can_pay = scenario(
        player(corporation="helion", megacredits=3, heat=3, hand=["sponsors"]), player()
    )
    assert offered(can_pay, "Play Sponsors")

    cannot = scenario(
        player(corporation="helion", megacredits=3, heat=2, hand=["sponsors"]), player()
    )
    assert not offered(cannot, "Play Sponsors")


def test_steel_and_heat_can_pay_together():
    game = scenario(
        player(
            corporation="helion", megacredits=0, steel=1, heat=2, hand=["nuclear_power"]
        ),
        player(),
    )
    assert not offered(game, "Play Nuclear Power")

    game = scenario(
        player(
            corporation="helion", megacredits=2, steel=1, heat=7, hand=["nuclear_power"]
        ),
        player(),
    )
    pick(game, "Play Nuclear Power")

    assert ways_to_pay(game) == [(2, 1, 0, 6), (1, 1, 0, 7)]


def test_more_heat_than_needed_is_never_paid():
    game = scenario(
        player(corporation="helion", megacredits=6, heat=20, hand=["sponsors"]),
        player(),
    )

    pick(game, "Play Sponsors")

    assert ways_to_pay(game) == [(6 - heat, 0, 0, heat) for heat in range(7)]


def test_another_player_may_not_pay_with_heat():
    game = scenario(
        player(megacredits=0, heat=6, hand=["sponsors"]), player(corporation="helion")
    )

    assert not offered(game, "Play Sponsors")


def test_local_heat_trapping_must_leave_its_5_heat_to_spend():
    too_little = scenario(
        player(
            corporation="helion", megacredits=0, heat=5, hand=["local_heat_trapping"]
        ),
        player(),
    )
    assert not offered(too_little, "Play Local Heat Trapping")

    enough = scenario(
        player(
            corporation="helion", megacredits=0, heat=6, hand=["local_heat_trapping"]
        ),
        player(),
    )
    pick(enough, "Play Local Heat Trapping")
    assert resources(enough, 0)["heat"] == 0

    with_megacredits = scenario(
        player(
            corporation="helion", megacredits=1, heat=5, hand=["local_heat_trapping"]
        ),
        player(),
    )
    pick(with_megacredits, "Play Local Heat Trapping")
    assert resources(with_megacredits, 0)["heat"] == 0
    assert resources(with_megacredits, 0)["megacredits"] == 0


def test_local_heat_trapping_is_not_offered_a_way_to_pay_that_spends_its_5_heat():
    game = scenario(
        player(
            corporation="helion", megacredits=1, heat=6, hand=["local_heat_trapping"]
        ),
        player(),
    )

    pick(game, "Play Local Heat Trapping")

    assert ways_to_pay(game) == [(1, 0, 0, 0), (0, 0, 0, 1)]


def test_a_standard_project_with_one_way_to_pay_is_paid_without_a_decision():
    game = scenario(
        player(corporation="helion", megacredits=10, heat=4), player(), temperature=-30
    )

    pick(game, "Asteroid (14 MegaCredits)")

    assert resources(game, 0)["megacredits"] == 0
    assert resources(game, 0)["heat"] == 0
    assert game.full_view()["temperature"] == -28
    assert "Player 1 pays 4 of it with heat." in game.log


def test_a_standard_project_with_several_ways_to_pay_asks_how():
    game = scenario(player(corporation="helion", megacredits=12, heat=4), player())

    pick(game, "Asteroid (14 MegaCredits)")

    assert game.decision["kind"] == "payment"
    assert ways_to_pay(game) == [(12, 0, 0, 2), (11, 0, 0, 3), (10, 0, 0, 4)]
    assert options(game)[0]["details"]["paying_for"] == "the Asteroid Standard Project"
    assert options(game)[0]["details"]["cost"] == 14
    assert labels(game)[0] == "Pay 12 MegaCredits and 2 heat"
    pick(game, type="payment", heat=3)
    assert resources(game, 0) == {
        "megacredits": 1,
        "steel": 0,
        "titanium": 0,
        "plants": 0,
        "energy": 0,
        "heat": 1,
    }
    assert game.full_view()["temperature"] == -28


def test_a_milestone_may_be_paid_with_heat():
    tiles = [{"area": area, "tile": "city", "owner": 0} for area in ("A1", "C3", "E7")]
    game = scenario(
        player(corporation="helion", megacredits=7, heat=2), player(), tiles=tiles
    )

    pick(game, "Claim the Mayor Milestone")
    assert ways_to_pay(game) == [(7, 0, 0, 1), (6, 0, 0, 2)]
    pick(game, type="payment", heat=2)

    assert resources(game, 0)["megacredits"] == 1
    assert resources(game, 0)["heat"] == 0
    assert game.full_view()["milestones"][1]["claimed_by"] == 0


def test_an_award_may_be_paid_with_heat():
    game = scenario(player(corporation="helion", megacredits=0, heat=8), player())

    pick(game, "Fund the Banker Award")

    assert resources(game, 0)["heat"] == 0
    assert game.full_view()["awards"][1]["funded_by"] == 0


def test_an_action_that_costs_megacredits_may_be_paid_with_heat():
    game = scenario(
        player(
            corporation="helion", megacredits=0, heat=7, played_cards=["space_mirrors"]
        ),
        player(),
    )

    pick(game, "Use the action of Space Mirrors")

    assert resources(game, 0)["heat"] == 0
    assert production(game, 0)["energy"] == 1


def test_cards_bought_in_a_research_phase_may_be_paid_with_heat_when_every_player_is_done():
    game = scenario(
        player(corporation="helion", megacredits=4, heat=5, **NO_INCOME),
        player(),
        draft=False,
        first_player=1,
    )
    end_the_action_phase(game)

    cards = player_board(game, 0)["buying"]["dealt"][:2]
    buy(game, *cards)
    assert game.decision["kind"] == "payment"
    assert ways_to_pay(game) == [(4, 0, 0, 2), (3, 0, 0, 3), (2, 0, 0, 4), (1, 0, 0, 5)]
    assert options(game)[0]["details"]["paying_for"] == "2 cards"
    pick(game, type="payment", heat=4)
    assert resources(game, 0)["heat"] == 5

    skip_buying(game)
    assert resources(game, 0)["megacredits"] == 2
    assert resources(game, 0)["heat"] == 1
    assert hand(game, 0) == cards


def test_how_a_player_pays_for_their_cards_stays_hidden_until_every_player_is_done():
    game = scenario(
        player(corporation="helion", megacredits=0, heat=6, **NO_INCOME),
        player(),
        draft=False,
        first_player=1,
    )
    end_the_action_phase(game)

    buy(game, player_board(game, 0)["buying"]["dealt"][0])

    assert game.decision["player"] == 1
    assert resources(game, 0)["heat"] == 6
    skip_buying(game)
    assert resources(game, 0)["heat"] == 3
    assert "Player 1 pays 3 of it with heat." in game.log


def test_what_a_player_may_buy_with_counts_their_heat():
    game = scenario(
        player(corporation="helion", megacredits=1, heat=3, **NO_INCOME),
        player(),
        draft=False,
        first_player=1,
    )
    end_the_action_phase(game)

    assert player_board(game, 0)["buying"]["megacredits"] == 4


def test_a_card_bought_with_an_action_may_be_paid_with_heat():
    game = scenario(
        player(
            corporation="helion",
            megacredits=1,
            heat=3,
            played_cards=["inventors_guild"],
        ),
        player(),
        deck=["mine"],
    )

    pick(game, "Use the action of Inventors' Guild")
    pick(game, type="buy_card", card="mine")

    assert game.decision["kind"] == "payment"
    assert ways_to_pay(game) == [(1, 0, 0, 2), (0, 0, 0, 3)]
    pick(game, type="payment", heat=3)
    assert hand(game, 0) == ["mine"]
    assert resources(game, 0) == {
        "megacredits": 1,
        "steel": 0,
        "titanium": 0,
        "plants": 0,
        "energy": 0,
        "heat": 0,
    }


def test_megacredits_may_not_be_used_as_heat():
    game = scenario(player(corporation="helion", megacredits=50, heat=7), player())

    assert not offered(game, "Convert 8 heat")
