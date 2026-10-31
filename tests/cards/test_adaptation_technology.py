"""#153 Adaptation Technology (12 MegaCredits, science Tag, 1 Victory Point): Effect: your global
requirements are +2 or -2 steps, your choice in each case."""

import pytest

from tests.helpers import final_scores, ocean, offered, pick, player, resources, scenario, terraformed_mars


def oceans(count):
    return [ocean(area) for area in ("A2", "A4", "A5", "B6", "D8", "E4", "E5", "E6", "F6")[:count]]


def test_adaptation_technology_has_no_requirements_and_costs_12_megacredits():
    game = scenario(player(megacredits=12, hand=["adaptation_technology"]), player())

    pick(game, "Play Adaptation Technology (12 MegaCredits)")

    assert resources(game, 0)["megacredits"] == 0


# Each case: a card, a Global Parameter 2 steps beyond its Requirement in the Player's favour, and
# the one beyond that. A Temperature step is 2 °C.
CASES = [
    ("breathing_filters", {"oxygen": 5}, {"oxygen": 4}),  # Oxygen 7 % or more
    ("colonizer_training_camp", {"oxygen": 7}, {"oxygen": 8}),  # Oxygen 5 % or less
    ("lichen", {"temperature": -28}, {"temperature": -30}),  # -24 °C or warmer
    ("archaebacteria", {"temperature": -14}, {"temperature": -12}),  # -18 °C or colder
    ("wave_power", {"tiles": oceans(1)}, {"tiles": oceans(0)}),  # 3 Oceans or more
    ("dust_seals", {"tiles": oceans(5)}, {"tiles": oceans(6)}),  # 3 Oceans or fewer
]


@pytest.mark.parametrize(("card", "within", "beyond"), CASES, ids=[case[0] for case in CASES])
def test_with_adaptation_technology_each_global_requirement_is_2_steps_easier(card, within, beyond):
    holding = player(megacredits=20, hand=[card], played_cards=["adaptation_technology"])
    without = player(megacredits=20, hand=[card])

    assert offered(scenario(holding, player(), **within), type="play_card", card=card)
    assert not offered(scenario(holding, player(), **beyond), type="play_card", card=card)
    assert not offered(scenario(without, player(), **within), type="play_card", card=card)


def test_adaptation_technology_does_not_change_a_tag_requirement():
    holding = player(megacredits=13, hand=["quantum_extractor"], played_cards=["adaptation_technology", "research"])

    assert not offered(scenario(holding, player()), "Play Quantum Extractor")


def test_adaptation_technology_is_worth_1_victory_point():
    game = scenario(player(played_cards=["adaptation_technology"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [1, 0]
