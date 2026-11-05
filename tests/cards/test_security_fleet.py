"""#028 Security Fleet (12 MegaCredits, space Tag): Action: spend 1 titanium to add 1 fighter to this
card. 1 Victory Point for each fighter on this card."""

from tests.helpers import (
    card_resources,
    final_scores,
    offered,
    pick,
    player,
    resources,
    scenario,
    terraformed_mars,
)


def test_it_has_no_requirement_and_holds_no_fighter_when_played():
    game = scenario(player(megacredits=12, hand=["security_fleet"]), player())

    pick(game, "Play Security Fleet (12 MegaCredits)")

    assert card_resources(game, 0) == {"security_fleet": 0}


def test_titanium_may_pay_for_it_as_a_space_card():
    playing = player(megacredits=9, titanium=1, hand=["security_fleet"])
    game = scenario(playing, player())

    pick(game, "Play Security Fleet")

    assert game.decision["kind"] == "action"
    assert resources(game, 0)["titanium"] == 0


def test_the_action_spends_1_titanium_to_add_1_fighter():
    playing = player(titanium=2, played_cards=["security_fleet"])
    game = scenario(playing, player())

    pick(game, "Use the action of Security Fleet")

    assert resources(game, 0)["titanium"] == 1
    assert card_resources(game, 0) == {"security_fleet": 1}
    assert "Player 1 adds 1 fighter to Security Fleet." in game.log
    assert not offered(game, "Use the action of Security Fleet")


def test_the_action_is_not_offered_without_titanium():
    game = scenario(player(played_cards=["security_fleet"]), player())

    assert not offered(game, "Use the action of Security Fleet")


def test_security_fleet_scores_1_victory_point_for_each_fighter():
    for fighters in (0, 1, 5):
        holding = player(
            played_cards=["security_fleet"], card_resources={"security_fleet": fighters}
        )

        game = scenario(holding, player(), **terraformed_mars())
        assert final_scores(game)[0]["cards"] == fighters
