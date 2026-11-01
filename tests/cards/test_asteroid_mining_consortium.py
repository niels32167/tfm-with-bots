"""#002 Asteroid Mining Consortium (13 MegaCredits, jovian Tag): requires that you have titanium
Production. Decrease any titanium Production 1 step and increase your own 1 step. 1 Victory
Point."""

from tests.helpers import final_scores, labels, offered, pick, player, production, scenario, terraformed_mars


def test_asteroid_mining_consortium_requires_titanium_production():
    assert not offered(
        scenario(player(hand=["asteroid_mining_consortium"]), player(production={"titanium": 1})),
        "Play Asteroid Mining Consortium",
    )
    game = scenario(player(hand=["asteroid_mining_consortium"], production={"titanium": 1}), player())
    assert offered(game, "Play Asteroid Mining Consortium (13 MegaCredits)")


def test_asteroid_mining_consortium_takes_a_titanium_production_step_from_the_opponent_picked():
    game = scenario(
        player(hand=["asteroid_mining_consortium"], production={"titanium": 1}),
        player(production={"titanium": 1}),
        player(production={"titanium": 2}),
    )

    pick(game, "Play Asteroid Mining Consortium")
    assert labels(game) == ["Lower Player 2's titanium Production by 1", "Lower Player 3's titanium Production by 1"]
    pick(game, "Player 3")

    assert [production(game, each)["titanium"] for each in range(3)] == [2, 1, 1]


def test_with_no_opponent_to_take_from_asteroid_mining_consortium_lowers_and_raises_the_players_own():
    game = scenario(player(hand=["asteroid_mining_consortium"], production={"titanium": 1}), player())

    pick(game, "Play Asteroid Mining Consortium")

    assert game.decision["kind"] == "action"
    assert production(game, 0)["titanium"] == 1
    assert "Player 1 lowers their own titanium Production by 1." in game.log


def test_asteroid_mining_consortium_is_worth_1_victory_point():
    game = scenario(player(played_cards=["asteroid_mining_consortium"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [1, 0]
