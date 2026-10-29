"""#155 Designed Microorganisms (16 MegaCredits, microbe and science Tags): it must be −14 °C or
colder. Increase your plant Production 2 steps."""

from tests.helpers import final_scores, offered, pick, player, production, resources, scenario, terraformed_mars


def test_designed_microorganisms_needs_minus_14_degrees_or_colder():
    holding = player(hand=["designed_microorganisms"])

    assert offered(scenario(holding, player(), temperature=-14), "Play Designed Microorganisms")
    assert not offered(scenario(holding, player(), temperature=-12), "Play Designed Microorganisms")


def test_designed_microorganisms_raises_plant_production_by_2():
    game = scenario(player(megacredits=16, hand=["designed_microorganisms"]), player())

    pick(game, "Play Designed Microorganisms (16 MegaCredits)")

    assert production(game, 0)["plants"] == 2
    assert resources(game, 0)["megacredits"] == 0


def test_designed_microorganisms_is_worth_no_victory_points():
    game = scenario(player(played_cards=["designed_microorganisms"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
