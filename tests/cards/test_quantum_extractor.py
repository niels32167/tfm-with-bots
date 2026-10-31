"""#079 Quantum Extractor (Corporate Era, 13 MegaCredits, power and science Tags): Effect: when you
play a Space card, you pay 2 MegaCredits less for it. Requires 4 science Tags. Increase your energy
Production 4 steps."""

from tests.helpers import final_scores, offered, pick, player, production, resources, scenario, terraformed_mars

# 4 science Tags: Research has 2.
FOUR_SCIENCE_TAGS = ["research", "inventors_guild", "development_center"]


def test_quantum_extractor_needs_4_science_tags():
    # Research and Inventors' Guild: 3 science Tags.
    three = player(megacredits=13, hand=["quantum_extractor"], played_cards=FOUR_SCIENCE_TAGS[:2] + ["mine"])

    assert not offered(scenario(three, player()), "Play Quantum Extractor")
    four = player(megacredits=13, hand=["quantum_extractor"], played_cards=FOUR_SCIENCE_TAGS)
    assert offered(scenario(four, player()), "Play Quantum Extractor")


def test_quantum_extractor_raises_energy_production_4_steps():
    game = scenario(player(megacredits=13, hand=["quantum_extractor"], played_cards=FOUR_SCIENCE_TAGS), player())

    pick(game, "Play Quantum Extractor (13 MegaCredits)")

    assert production(game, 0)["energy"] == 4
    assert resources(game, 0)["megacredits"] == 0


def test_with_quantum_extractor_a_card_with_a_space_tag_costs_2_megacredits_less():
    game = scenario(
        player(megacredits=8, hand=["satellites", "sponsors"], played_cards=["quantum_extractor"]), player()
    )

    assert offered(game, "Play Satellites (8 MegaCredits)")
    assert offered(game, "Play Sponsors (6 MegaCredits)")


def test_quantum_extractor_is_worth_no_victory_points():
    game = scenario(player(played_cards=["quantum_extractor"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
