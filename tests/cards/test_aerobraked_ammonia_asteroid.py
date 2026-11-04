"""#170 Aerobraked Ammonia Asteroid (26 MegaCredits, space and Event Tags): add 2 microbes to ANOTHER
card. Raise your heat Production 3 steps and your plant Production 1 step."""

from tests.helpers import card_resources, labels, pick, player, production, scenario


def test_it_raises_production_and_adds_2_microbes_to_the_only_card_that_holds_them_without_a_decision():
    game = scenario(
        player(
            megacredits=26,
            hand=["aerobraked_ammonia_asteroid"],
            played_cards=["tardigrades"],
        ),
        player(),
    )

    pick(game, "Play Aerobraked Ammonia Asteroid (26 MegaCredits)")

    assert (production(game, 0)["heat"], production(game, 0)["plants"]) == (3, 1)
    assert card_resources(game, 0) == {"tardigrades": 2}
    assert "Player 1 adds 2 microbes to Tardigrades." in game.log
    assert game.decision["kind"] == "action"


def test_with_several_cards_that_hold_microbes_the_player_picks_one():
    played = ["regolith_eaters", "tardigrades", "physics_complex"]
    game = scenario(
        player(
            megacredits=26, hand=["aerobraked_ammonia_asteroid"], played_cards=played
        ),
        player(),
    )

    pick(game, "Play Aerobraked Ammonia Asteroid")

    assert game.decision["kind"] == "add_to_card"
    assert labels(game) == [
        "Add 2 microbes to Regolith Eaters",
        "Add 2 microbes to Tardigrades",
    ]
    pick(game, type="add_card_resources", to="tardigrades", amount=2, kind="microbe")
    assert card_resources(game, 0) == {
        "physics_complex": 0,
        "regolith_eaters": 0,
        "tardigrades": 2,
    }
    assert game.decision["kind"] == "action"


def test_without_a_card_that_holds_microbes_it_can_still_be_played_and_the_microbes_are_lost():
    game = scenario(
        player(megacredits=26, hand=["aerobraked_ammonia_asteroid"]),
        player(played_cards=["tardigrades"]),
    )

    pick(game, "Play Aerobraked Ammonia Asteroid")

    assert production(game, 0)["heat"] == 3
    assert card_resources(game, 1) == {"tardigrades": 0}
    assert "Player 1 has no card to add 2 microbes to." in game.log
    assert game.decision["kind"] == "action"
