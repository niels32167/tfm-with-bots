"""#124 Hired Raiders (1 MegaCredit, Event Tag): steal up to 2 steel, or 3 MegaCredits, from any
Player."""

from tests.helpers import final_scores, labels, pick, player, resources, scenario, terraformed_mars


def test_hired_raiders_offers_to_steal_steel_or_megacredits_from_each_opponent_or_nothing():
    game = scenario(player(megacredits=1, hand=["hired_raiders"]), player(megacredits=2, steel=5))

    pick(game, "Play Hired Raiders (1 MegaCredit)")

    assert labels(game) == ["Steal 2 steel from Player 2", "Steal 2 MegaCredits from Player 2", "Steal nothing"]


def test_hired_raiders_gains_what_it_steals():
    game = scenario(player(megacredits=1, hand=["hired_raiders"]), player(megacredits=2, steel=5))

    pick(game, "Play Hired Raiders")
    pick(game, "Steal 2 steel from Player 2")

    assert resources(game, 0)["steel"] == 2
    assert resources(game, 1)["steel"] == 3
    assert "Player 1 steals 2 steel from Player 2." in game.log


def test_stealing_nothing_with_hired_raiders_changes_nobodys_resources():
    game = scenario(player(megacredits=1, hand=["hired_raiders"]), player(megacredits=2, steel=5))

    pick(game, "Play Hired Raiders")
    pick(game, "Steal nothing")

    assert (resources(game, 0)["megacredits"], resources(game, 0)["steel"]) == (0, 0)
    assert (resources(game, 1)["megacredits"], resources(game, 1)["steel"]) == (2, 5)
    assert "Player 1 steals nothing with Hired Raiders." in game.log


def test_hired_raiders_has_no_victory_points():
    game = scenario(player(played_cards=["hired_raiders"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
