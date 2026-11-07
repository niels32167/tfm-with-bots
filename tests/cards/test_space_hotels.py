"""#P42 Space Hotels (Prelude's Project Card, 12 MegaCredits, space and Earth Tags): requires 2 Earth Tags. Increase
your MegaCredit Production 4 steps."""

from tests.helpers import final_scores, offered, pick, player, production, scenario, terraformed_mars


def test_space_hotels_needs_2_earth_tags():
    one = scenario(player(megacredits=12, hand=["space_hotels"], played_cards=["sponsors"]), player(), prelude=True)
    two = scenario(
        player(megacredits=12, hand=["space_hotels"], played_cards=["sponsors", "cartel"]),
        player(),
        prelude=True,
    )

    assert not offered(one, "Play Space Hotels")
    assert offered(two, "Play Space Hotels (12 MegaCredits)")


def test_space_hotels_raises_megacredit_production_4_steps_and_titanium_may_pay_for_it():
    game = scenario(
        player(megacredits=0, titanium=4, hand=["space_hotels"], played_cards=["sponsors", "cartel"]),
        player(),
        prelude=True,
    )

    pick(game, "Play Space Hotels")

    assert production(game, 0)["megacredits"] == 4
    assert "Player 1 plays Space Hotels, paying 4 titanium." in game.log


def test_space_hotels_is_worth_no_victory_points():
    game = scenario(player(played_cards=["space_hotels"]), player(), prelude=True, **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
