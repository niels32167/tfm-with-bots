"""Cheung Shing Mars (Prelude's Corporation, building Tag): Effect: when you play a building Tag, you pay 2
MegaCredits less for it. You start with 3 MegaCredit Production and 44 MegaCredits."""

import pytest

from tests.helpers import card_costs, pick, player, player_board, production, resources, scenario, start_as


def test_cheung_shing_mars_starts_with_44_megacredits_3_megacredit_production_and_a_building_tag():
    game, first = start_as("cheung_shing_mars", prelude=True)

    assert resources(game, first)["megacredits"] == 44
    assert production(game, first)["megacredits"] == 3
    assert player_board(game, first)["tags"]["building"] == 1


def test_a_card_with_a_building_tag_costs_2_megacredits_less_and_others_do_not():
    game = scenario(
        player(corporation="cheung_shing_mars", megacredits=2, hand=["mine", "sponsors"]), player(), prelude=True
    )

    assert card_costs(game, 0) == {"mine": 2, "sponsors": 6}
    pick(game, "Play Mine (2 MegaCredits)")
    assert resources(game, 0)["megacredits"] == 0


def test_a_scenario_names_it_only_with_prelude():
    with pytest.raises(ValueError, match="'cheung_shing_mars' is a card of the Prelude box, and the Scenario has no"):
        scenario(player(corporation="cheung_shing_mars"), player())

