"""#150 Anti-Gravity Technology (Corporate Era, 14 MegaCredits, science Tag, 3 Victory Points):
Effect: when you play a card, you pay 2 MegaCredits less for it. Requires 7 science Tags."""

from tests.helpers import final_scores, offered, pick, player, resources, scenario, terraformed_mars

# 7 science Tags: Research has 2.
SEVEN_SCIENCE_TAGS = [
    "research",
    "inventors_guild",
    "development_center",
    "solar_wind_power",
    "gene_repair",
    "medical_lab",
]


def test_anti_gravity_technology_needs_7_science_tags():
    six = player(
        megacredits=14, hand=["anti_gravity_technology"], played_cards=SEVEN_SCIENCE_TAGS[1:] + ["fusion_power"]
    )
    seven = player(megacredits=14, hand=["anti_gravity_technology"], played_cards=SEVEN_SCIENCE_TAGS)

    assert not offered(scenario(six, player()), "Play Anti-Gravity Technology")
    game = scenario(seven, player())
    pick(game, "Play Anti-Gravity Technology (14 MegaCredits)")
    assert resources(game, 0)["megacredits"] == 0


def test_with_anti_gravity_technology_every_card_costs_2_megacredits_less():
    game = scenario(
        player(megacredits=4, hand=["mine", "sponsors"], played_cards=["anti_gravity_technology"]), player()
    )

    assert offered(game, "Play Mine (2 MegaCredits)")
    assert offered(game, "Play Sponsors (4 MegaCredits)")


def test_anti_gravity_technology_is_worth_3_victory_points():
    game = scenario(player(played_cards=["anti_gravity_technology"]), player(), **terraformed_mars())

    assert [score["cards"] for score in final_scores(game)] == [3, 0]
