"""#023 Arctic Algae (12 MegaCredits, plant Tag): Effect: when anyone places an Ocean Tile, gain 2
plants. It must be -12 °C or colder to play. Gain 1 plant."""

from tests.helpers import final_scores, offered, pick, player, resources, scenario, terraformed_mars


def test_arctic_algae_must_be_played_at_minus_12_degrees_or_colder():
    holding = player(megacredits=12, hand=["arctic_algae"])

    assert offered(scenario(holding, player(), temperature=-12), "Play Arctic Algae")
    assert not offered(scenario(holding, player(), temperature=-10), "Play Arctic Algae")


def test_arctic_algae_gains_1_plant():
    game = scenario(player(megacredits=12, hand=["arctic_algae"]), player())

    pick(game, "Play Arctic Algae (12 MegaCredits)")

    assert resources(game, 0)["plants"] == 1
    assert resources(game, 0)["megacredits"] == 0


def test_with_arctic_algae_its_player_gains_2_plants_for_their_own_ocean():
    game = scenario(player(megacredits=18, played_cards=["arctic_algae"]), player())

    pick(game, "Aquifer")
    pick(game, "Place the Ocean on A4")

    assert resources(game, 0)["plants"] == 2
    assert "Player 1's Arctic Algae takes effect." in game.log
    assert "Player 1 gains 2 plants." in game.log


def test_with_arctic_algae_its_player_gains_2_plants_for_another_players_ocean_too():
    game = scenario(player(megacredits=18), player(played_cards=["arctic_algae"]))

    pick(game, "Aquifer")
    pick(game, "Place the Ocean on A4")

    assert resources(game, 1)["plants"] == 2
    assert resources(game, 0)["plants"] == 0


def test_arctic_algae_gains_2_plants_for_each_ocean_a_card_places():
    game = scenario(player(megacredits=23, hand=["ice_asteroid"], played_cards=["arctic_algae"]), player())

    pick(game, "Play Ice Asteroid")
    pick(game, "Place the Ocean on A4")
    pick(game, "Place the Ocean on A5")

    assert resources(game, 0)["plants"] == 4


def test_arctic_algae_is_worth_no_victory_points():
    game = scenario(player(played_cards=["arctic_algae"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
