"""#086 Robotic Workforce (Corporate Era, 9 MegaCredits, science Tag): duplicate only the
production box of one of your building cards."""

from tests.helpers import (
    final_scores,
    labels,
    offered,
    pick,
    player,
    production,
    resources,
    scenario,
    terraformed_mars,
)


def test_robotic_workforce_needs_a_building_card_of_your_own_with_a_production_box():
    # Research has no building Tag, Colonizer Training Camp no production box, and the other
    # Player's Mine is not yours.
    without = player(hand=["robotic_workforce"], played_cards=["research", "colonizer_training_camp"])
    assert not offered(scenario(without, player(played_cards=["mine"])), "Play Robotic Workforce")
    with_mine = player(hand=["robotic_workforce"], played_cards=["mine"])
    assert offered(scenario(with_mine, player()), "Play Robotic Workforce")


def test_robotic_workforce_needs_a_production_box_it_can_copy_in_full():
    # Carbonate Processing lowers energy Production 1 step.
    holding = player(hand=["robotic_workforce"], played_cards=["carbonate_processing"])
    assert not offered(scenario(holding, player()), "Play Robotic Workforce")
    assert offered(scenario({**holding, "production": {"energy": 1}}, player()), "Play Robotic Workforce")


def test_with_one_building_card_to_copy_robotic_workforce_copies_its_production_box_at_once():
    holding = player(megacredits=9, hand=["robotic_workforce"], played_cards=["carbonate_processing"])
    game = scenario({**holding, "production": {"energy": 1}}, player())

    pick(game, "Play Robotic Workforce (9 MegaCredits)")

    assert production(game, 0)["energy"] == 0
    assert production(game, 0)["heat"] == 3
    assert "Player 1 copies the production box of Carbonate Processing." in game.log
    assert game.decision["kind"] == "action"


def test_robotic_workforce_asks_which_building_card_to_copy_leaving_out_those_it_cannot():
    # Tropical Resort lowers heat Production 2 steps, which this Player doesn't have.
    played = ["mine", "tropical_resort", "geothermal_power"]
    game = scenario(player(hand=["robotic_workforce"], played_cards=played), player())

    pick(game, "Play Robotic Workforce")

    assert game.decision["kind"] == "production"
    assert labels(game) == ["Copy the production box of Mine", "Copy the production box of Geothermal Power"]
    assert offered(game, type="copy_production_box", card="geothermal_power")
    pick(game, "Copy the production box of Geothermal Power")
    assert production(game, 0)["energy"] == 2
    assert production(game, 0)["steel"] == 0
    assert game.decision["kind"] == "action"


def test_robotic_workforce_copies_only_the_production_box_not_the_cards_other_effects():
    # Open City also gives 2 plants and places a City.
    holding = player(hand=["robotic_workforce"], played_cards=["open_city"], production={"energy": 1})
    game = scenario(holding, player())

    pick(game, "Play Robotic Workforce")

    assert production(game, 0)["energy"] == 0
    assert production(game, 0)["megacredits"] == 4
    assert resources(game, 0)["plants"] == 0
    assert game.decision["kind"] == "action"


def test_robotic_workforce_offers_every_card_in_card_number_order_even_two_with_the_same_box():
    # Solar Power (#113) and Power Plant (#141) each raise energy Production 1 step.
    game = scenario(player(hand=["robotic_workforce"], played_cards=["power_plant", "solar_power"]), player())

    pick(game, "Play Robotic Workforce")

    assert labels(game) == ["Copy the production box of Solar Power", "Copy the production box of Power Plant"]


def test_robotic_workforce_is_worth_no_victory_points():
    game = scenario(player(played_cards=["robotic_workforce"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]


def test_robotic_workforce_may_copy_the_production_box_of_a_played_prelude_card_with_a_building_tag():
    # Mining Operations is a building card too; Power Generation has no building Tag.
    holding = player(hand=["robotic_workforce"], played_prelude_cards=["mining_operations", "power_generation"])
    game = scenario(holding, player(), prelude=True)

    pick(game, "Play Robotic Workforce")

    assert production(game, 0)["steel"] == 2
    assert resources(game, 0)["steel"] == 0
