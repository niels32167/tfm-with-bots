"""#094 Mass Converter (Corporate Era, 8 MegaCredits, power and science Tags): Effect: when you play
a Space card, you pay 2 MegaCredits less for it. Requires 5 science Tags. Increase your energy
Production 6 steps."""

from tests.helpers import final_scores, offered, pick, player, production, resources, scenario, terraformed_mars

# 5 science Tags: Research has 2.
FIVE_SCIENCE_TAGS = ["research", "inventors_guild", "development_center", "gene_repair"]


def test_mass_converter_needs_5_science_tags():
    # Research, Inventors' Guild and Development Center: 4 science Tags.
    four = player(megacredits=8, hand=["mass_converter"], played_cards=FIVE_SCIENCE_TAGS[:3] + ["mine"])

    assert not offered(scenario(four, player()), "Play Mass Converter")
    five = player(megacredits=8, hand=["mass_converter"], played_cards=FIVE_SCIENCE_TAGS)
    assert offered(scenario(five, player()), "Play Mass Converter")


def test_mass_converter_raises_energy_production_6_steps():
    game = scenario(player(megacredits=8, hand=["mass_converter"], played_cards=FIVE_SCIENCE_TAGS), player())

    pick(game, "Play Mass Converter (8 MegaCredits)")

    assert production(game, 0)["energy"] == 6
    assert resources(game, 0)["megacredits"] == 0


def test_with_mass_converter_a_card_with_a_space_tag_costs_2_megacredits_less():
    game = scenario(player(megacredits=8, hand=["satellites", "sponsors"], played_cards=["mass_converter"]), player())

    assert offered(game, "Play Satellites (8 MegaCredits)")
    assert offered(game, "Play Sponsors (6 MegaCredits)")


def test_mass_converter_is_worth_no_victory_points():
    game = scenario(player(played_cards=["mass_converter"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [0, 0]
