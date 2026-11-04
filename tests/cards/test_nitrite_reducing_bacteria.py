"""#157 Nitrite Reducing Bacteria (11 MegaCredits, microbe Tag): add 3 microbes to this card. Action:
add 1 microbe to this card, or remove 3 microbes to raise your Terraform Rating 1 step."""

from tests.helpers import card_resources, labels, pick, player, player_board, scenario


def test_nitrite_reducing_bacteria_comes_with_3_microbes():
    game = scenario(
        player(megacredits=11, hand=["nitrite_reducing_bacteria"]), player()
    )

    pick(game, "Play Nitrite Reducing Bacteria (11 MegaCredits)")

    assert card_resources(game, 0) == {"nitrite_reducing_bacteria": 3}
    assert "Player 1 adds 3 microbes to Nitrite Reducing Bacteria." in game.log


def test_with_fewer_than_3_microbes_the_action_just_adds_one():
    holding = player(
        played_cards=["nitrite_reducing_bacteria"],
        card_resources={"nitrite_reducing_bacteria": 2},
    )
    game = scenario(holding, player())

    pick(game, "Use the action of Nitrite Reducing Bacteria")

    assert card_resources(game, 0) == {"nitrite_reducing_bacteria": 3}
    assert game.decision["kind"] == "action"


def test_removing_3_microbes_raises_the_terraform_rating_1_step():
    holding = player(
        played_cards=["nitrite_reducing_bacteria"],
        card_resources={"nitrite_reducing_bacteria": 4},
    )
    game = scenario(holding, player())

    pick(game, "Use the action of Nitrite Reducing Bacteria")
    assert labels(game) == [
        "Add 1 microbe to Nitrite Reducing Bacteria",
        "Remove 3 microbes from Nitrite Reducing Bacteria to raise your Terraform Rating 1 step",
    ]
    pick(game, "Remove 3 microbes")

    assert card_resources(game, 0) == {"nitrite_reducing_bacteria": 1}
    assert player_board(game, 0)["terraform_rating"] == 21
