"""#121 Sabotage (1 MegaCredit, Event Tag): remove up to 3 titanium from any Player, or 4 steel, or 7
MegaCredits."""

from tests.helpers import final_scores, labels, pick, player, resources, scenario, terraformed_mars


def test_sabotage_offers_each_resource_each_opponent_has_up_to_its_amount_and_nothing():
    game = scenario(
        player(megacredits=1, titanium=5, hand=["sabotage"]),
        player(megacredits=10, titanium=2),
        player(megacredits=0, steel=6),
    )

    pick(game, "Play Sabotage (1 MegaCredit)")

    assert labels(game) == [
        "Remove 2 titanium from Player 2",
        "Remove 7 MegaCredits from Player 2",
        "Remove 4 steel from Player 3",
        "Remove nothing",
    ]


def test_sabotage_removes_the_resource_picked():
    game = scenario(player(megacredits=1, hand=["sabotage"]), player(megacredits=10, steel=4))

    pick(game, "Play Sabotage")
    pick(game, "Remove 7 MegaCredits from Player 2")

    assert (resources(game, 1)["megacredits"], resources(game, 1)["steel"]) == (3, 4)
    assert resources(game, 0)["megacredits"] == 0


def test_sabotage_with_nobody_to_take_from_is_played_for_nothing_without_a_decision():
    game = scenario(player(megacredits=1, hand=["sabotage"]), player(megacredits=0))

    pick(game, "Play Sabotage")

    assert game.decision["kind"] == "action"


def test_sabotage_has_no_victory_points():
    game = scenario(player(played_cards=["sabotage"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
