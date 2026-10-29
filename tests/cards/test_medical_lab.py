"""#207 Medical Lab (Corporate Era, 13 MegaCredits, building and science Tags, 1 Victory Point):
increase your MegaCredit Production 1 step for every 2 building Tags you have, including this."""

from tests.helpers import final_scores, pick, player, production, resources, scenario, terraformed_mars


def test_medical_lab_raises_megacredit_production_by_1_for_every_2_building_tags_including_its_own():
    # Mine and Deep Well Heating have a building Tag each: with Medical Lab's own that makes 3.
    played = ["mine", "deep_well_heating"]
    game = scenario(player(megacredits=13, hand=["medical_lab"], played_cards=played), player())

    pick(game, "Play Medical Lab (13 MegaCredits)")

    assert production(game, 0)["megacredits"] == 1
    assert resources(game, 0)["megacredits"] == 0
    assert "Player 1 raises their MegaCredit Production by 1." in game.log


def test_medical_lab_with_its_own_building_tag_and_one_more_raises_megacredit_production_by_1():
    game = scenario(player(hand=["medical_lab"], played_cards=["mine"]), player())

    pick(game, "Play Medical Lab")

    assert production(game, 0)["megacredits"] == 1


def test_medical_lab_with_only_its_own_building_tag_raises_nothing():
    game = scenario(player(hand=["medical_lab"]), player())

    pick(game, "Play Medical Lab")

    assert production(game, 0)["megacredits"] == 0


def test_robotic_workforce_copying_medical_lab_counts_the_building_tags_again():
    # Medical Lab, Mine, Deep Well Heating and Colonizer Training Camp make 4 building Tags.
    played = ["medical_lab", "mine", "deep_well_heating", "colonizer_training_camp"]
    game = scenario(player(hand=["robotic_workforce"], played_cards=played), player())

    pick(game, "Play Robotic Workforce")
    pick(game, "Copy the production box of Medical Lab")

    assert production(game, 0)["megacredits"] == 2
    assert "Player 1 copies the production box of Medical Lab." in game.log


def test_medical_lab_is_worth_1_victory_point():
    game = scenario(player(played_cards=["medical_lab"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [1, 0]
