"""#007 Martian Rails (13 MegaCredits, building Tag): Action: spend 1 energy to gain 1 MegaCredit
for each City Tile on Mars."""

from tests.helpers import city, final_scores, offered, pick, player, resources, scenario, terraformed_mars


def test_martian_rails_has_no_requirements_and_does_nothing_when_played():
    game = scenario(player(megacredits=13, hand=["martian_rails"]), player())

    pick(game, "Play Martian Rails (13 MegaCredits)")

    assert resources(game, 0)["megacredits"] == 0


def test_martian_rails_action_gains_1_megacredit_for_each_city_on_mars_whoever_owns_it():
    cities = [city("A1", owner=0), city("C3", owner=1), city("G2", owner=1)]
    game = scenario(player(megacredits=0, energy=2, played_cards=["martian_rails"]), player(), tiles=cities)

    pick(game, "Use the action of Martian Rails")

    assert resources(game, 0)["energy"] == 1
    assert resources(game, 0)["megacredits"] == 3
    assert "Player 1 gains 3 MegaCredits." in game.log


def test_martian_rails_action_with_no_city_on_mars_gains_nothing_but_is_still_offered():
    game = scenario(player(megacredits=0, energy=1, played_cards=["martian_rails"]), player())

    pick(game, "Use the action of Martian Rails")

    assert resources(game, 0)["energy"] == 0
    assert resources(game, 0)["megacredits"] == 0


def test_martian_rails_action_needs_1_energy():
    assert not offered(scenario(player(played_cards=["martian_rails"]), player()), type="use_action")


def test_martian_rails_has_no_victory_points():
    game = scenario(player(played_cards=["martian_rails"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
