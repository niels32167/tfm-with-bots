"""#P24 Nitrogen Shipment (Prelude Card): increase your plant Production 1 step. Increase your
Terraform Rating 1 step. Gain 5 MegaCredits."""

from tests.helpers import player, player_board, production, resources, scenario


def test_nitrogen_shipment_raises_plant_production_and_terraform_rating_and_gains_5_megacredits():
    game = scenario(player(prelude_cards=["nitrogen_shipment"]), player(), prelude=True)

    assert production(game, 0)["plants"] == 1
    assert player_board(game, 0)["terraform_rating"] == 21
    assert resources(game, 0)["megacredits"] == 47
