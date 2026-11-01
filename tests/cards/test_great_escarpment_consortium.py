"""#061 Great Escarpment Consortium (6 MegaCredits): requires that you have steel Production.
Decrease any steel Production 1 step and increase your own 1 step."""

from tests.helpers import final_scores, offered, pick, player, production, scenario, terraformed_mars


def test_great_escarpment_consortium_requires_steel_production():
    game = scenario(player(hand=["great_escarpment_consortium"]), player(production={"steel": 1}))
    assert not offered(game, "Play Great Escarpment Consortium")
    game = scenario(player(hand=["great_escarpment_consortium"], production={"steel": 1}), player())
    assert offered(game, "Play Great Escarpment Consortium (6 MegaCredits)")


def test_great_escarpment_consortium_takes_a_steel_production_step_from_the_only_opponent_with_some():
    game = scenario(
        player(hand=["great_escarpment_consortium"], production={"steel": 1}), player(production={"steel": 3})
    )

    pick(game, "Play Great Escarpment Consortium")

    assert game.decision["kind"] == "action"
    assert production(game, 0)["steel"] == 2
    assert production(game, 1)["steel"] == 2
    assert "Player 1 lowers Player 2's steel Production by 1." in game.log


def test_great_escarpment_consortium_has_no_victory_points():
    game = scenario(player(played_cards=["great_escarpment_consortium"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
