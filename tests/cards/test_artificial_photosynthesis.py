"""#115 Artificial Photosynthesis (12 MegaCredits, science Tag): increase your plant Production 1
step or your energy Production 2 steps."""

from tests.helpers import final_scores, labels, offered, pick, player, production, resources, scenario, terraformed_mars


def test_artificial_photosynthesis_asks_whether_to_raise_plant_or_energy_production():
    game = scenario(player(megacredits=12, hand=["artificial_photosynthesis"]), player())

    pick(game, "Play Artificial Photosynthesis (12 MegaCredits)")

    assert resources(game, 0)["megacredits"] == 0
    assert game.decision["kind"] == "production"
    assert labels(game) == ["Raise plant Production by 1", "Raise energy Production by 2"]
    assert offered(game, type="choose_production", card="artificial_photosynthesis")


def test_artificial_photosynthesis_raising_plant_production():
    game = scenario(player(hand=["artificial_photosynthesis"]), player())

    pick(game, "Play Artificial Photosynthesis")
    pick(game, "Raise plant Production by 1")

    assert production(game, 0)["plants"] == 1
    assert production(game, 0)["energy"] == 0
    assert "Player 1 raises their plant Production by 1." in game.log
    assert game.decision["kind"] == "action"


def test_artificial_photosynthesis_raising_energy_production():
    game = scenario(player(hand=["artificial_photosynthesis"]), player())

    pick(game, "Play Artificial Photosynthesis")
    pick(game, "Raise energy Production by 2")

    assert production(game, 0)["energy"] == 2
    assert production(game, 0)["plants"] == 0
    assert game.decision["kind"] == "action"


def test_artificial_photosynthesis_is_worth_no_victory_points():
    game = scenario(player(played_cards=["artificial_photosynthesis"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
