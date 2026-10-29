"""#135 Advanced Ecosystems (11 MegaCredits, animal, microbe and plant Tags, 3 Victory Points):
requires a plant Tag, a microbe Tag and an animal Tag."""

from tests.helpers import final_scores, offered, pick, player, resources, scenario, terraformed_mars


def test_advanced_ecosystems_needs_a_plant_a_microbe_and_an_animal_tag():
    # Algae has a plant Tag, Ants a microbe Tag and Birds an animal Tag.
    for played in (["ants", "birds"], ["algae", "birds"], ["algae", "ants"]):
        assert not offered(
            scenario(player(hand=["advanced_ecosystems"], played_cards=played), player()), "Play Advanced Ecosystems"
        )
    every_tag = player(hand=["advanced_ecosystems"], played_cards=["algae", "ants", "birds"])
    assert offered(scenario(every_tag, player()), "Play Advanced Ecosystems")


def test_advanced_ecosystems_own_tags_do_not_meet_its_requirements():
    assert not offered(scenario(player(hand=["advanced_ecosystems"]), player()), "Play Advanced Ecosystems")


def test_advanced_ecosystems_only_costs_its_megacredits():
    game = scenario(
        player(megacredits=11, hand=["advanced_ecosystems"], played_cards=["algae", "ants", "birds"]), player()
    )

    pick(game, "Play Advanced Ecosystems (11 MegaCredits)")

    assert resources(game, 0)["megacredits"] == 0
    assert game.decision["kind"] == "action"


def test_advanced_ecosystems_is_worth_3_victory_points():
    game = scenario(player(played_cards=["advanced_ecosystems"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [3, 0]
