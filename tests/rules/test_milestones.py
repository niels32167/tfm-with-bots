"""Milestones: a Player who meets one may claim it as an Action for 8 MegaCredits. Each is
claimed once, and only three per Game."""

from tests.helpers import (
    PROJECT_CARDS,
    city,
    claimed,
    greenery,
    milestone,
    offered,
    pick,
    player,
    player_board,
    resources,
    scenario,
)


def test_a_player_with_a_terraform_rating_of_35_may_claim_terraformer_for_8_megacredits():
    game = scenario(player(megacredits=10, terraform_rating=35), player())

    pick(game, "Claim the Terraformer Milestone")

    assert resources(game, 0)["megacredits"] == 2
    assert milestone(game, "terraformer")["claimed_by"] == 0
    assert "Player 1 claims the Terraformer Milestone for 8 MegaCredits." in game.log
    assert player_board(game, 0)["terraform_rating"] == 35  # a Milestone scores only at the end


def test_terraformer_is_not_offered_below_a_terraform_rating_of_35():
    game = scenario(player(terraform_rating=34), player())

    assert not offered(game, "Claim the Terraformer Milestone")
    assert milestone(game, "terraformer")["counts"] == [34, 20]


def test_mayor_needs_3_cities_of_the_players_own():
    two_cities = [city("A1", 0), city("C3", 0), city("G1", 1)]
    game = scenario(player(), player(), tiles=two_cities)
    assert not offered(game, "Claim the Mayor Milestone")
    assert milestone(game, "mayor")["counts"] == [2, 1]

    game = scenario(player(), player(), tiles=[*two_cities, city("J1", 0)])
    pick(game, "Claim the Mayor Milestone")
    assert milestone(game, "mayor")["claimed_by"] == 0


def test_gardener_needs_3_greeneries_of_the_players_own():
    two_greeneries = [greenery("A1", 0), greenery("A3", 0), greenery("B1", 1)]
    game = scenario(player(), player(), tiles=two_greeneries)
    assert not offered(game, "Claim the Gardener Milestone")
    assert milestone(game, "gardener")["counts"] == [2, 1]

    game = scenario(player(), player(), tiles=[*two_greeneries, greenery("J1", 0)])
    pick(game, "Claim the Gardener Milestone")
    assert milestone(game, "gardener")["claimed_by"] == 0


# Seven cards with one building Tag each, none of them Events.
SEVEN_BUILDING_TAGS = [
    "mine",
    "power_plant",
    "nuclear_power",
    "solar_power",
    "strip_mine",
    "titanium_mine",
    "windmills",
]


def test_builder_needs_8_building_tags_in_play():
    game = scenario(player(played_cards=SEVEN_BUILDING_TAGS, hand=["colonizer_training_camp"]), player())
    assert not offered(game, "Claim the Builder Milestone")
    assert milestone(game, "builder")["counts"] == [7, 0]

    game = scenario(player(played_cards=[*SEVEN_BUILDING_TAGS, "colonizer_training_camp"]), player())
    pick(game, "Claim the Builder Milestone")
    assert milestone(game, "builder")["claimed_by"] == 0


def test_planner_needs_16_cards_in_hand():
    game = scenario(player(hand=PROJECT_CARDS[:15]), player(hand=PROJECT_CARDS[15:17]))
    assert not offered(game, "Claim the Planner Milestone")
    assert milestone(game, "planner")["counts"] == [15, 2]

    game = scenario(player(hand=PROJECT_CARDS[:16]), player())
    pick(game, "Claim the Planner Milestone")
    assert milestone(game, "planner")["claimed_by"] == 0


def test_a_claimed_planner_stays_claimed_after_the_hand_shrinks():
    game = scenario(player(hand=[*PROJECT_CARDS[:15], "mine"]), player())
    pick(game, "Claim the Planner Milestone")

    pick(game, "Play Mine")

    assert milestone(game, "planner")["counts"] == [15, 0]
    assert milestone(game, "planner")["claimed_by"] == 0


def test_a_milestone_is_not_offered_without_8_megacredits():
    game = scenario(player(megacredits=7, terraform_rating=35), player())

    assert not offered(game, "Claim the Terraformer Milestone")


def test_claiming_a_milestone_is_one_of_the_two_actions_of_a_turn():
    game = scenario(player(megacredits=16, terraform_rating=35), player())

    pick(game, "Claim the Terraformer Milestone")

    assert game.decision["player"] == 0
    assert game.player_view(0)["actions_this_turn"] == 1
    assert offered(game, "End Turn")


def test_a_claim_option_names_the_milestone_and_its_cost():
    game = scenario(player(terraform_rating=35), player())

    found = [option for option in game.decision["options"] if option["details"]["type"] == "claim_milestone"]

    assert [(option["label"], option["details"]) for option in found] == [
        (
            "Claim the Terraformer Milestone (8 MegaCredits)",
            {"type": "claim_milestone", "milestone": "terraformer", "cost": 8},
        )
    ]


def test_everyone_sees_each_milestone_with_its_condition_and_target():
    game = scenario(player(), player())

    milestones = game.player_view(1)["milestones"]

    assert [(entry["name"], entry["condition"], entry["target"]) for entry in milestones] == [
        ("Terraformer", "Having a Terraform Rating of at least 35", 35),
        ("Mayor", "Owning at least 3 Cities", 3),
        ("Gardener", "Owning at least 3 Greeneries", 3),
        ("Builder", "Having at least 8 building Tags in play", 8),
        ("Planner", "Having at least 16 cards in hand", 16),
    ]
    assert all(entry["claimed_by"] is None for entry in milestones)
    assert game.player_view(1)["milestone_cost"] == 8


def test_each_milestone_can_be_claimed_only_once():
    game = scenario(player(terraform_rating=35), player(), milestones=[claimed("terraformer", by=1)])

    assert not offered(game, "Claim the Terraformer Milestone")
    assert milestone(game, "terraformer")["claimed_by"] == 1


def test_only_three_milestones_can_be_claimed_per_game():
    three_claimed = [claimed("mayor", by=1), claimed("gardener", by=1), claimed("planner", by=0)]
    game = scenario(player(terraform_rating=35), player(), milestones=three_claimed)

    assert not offered(game, "Claim the Terraformer Milestone")
    assert game.player_view(0)["milestone_cost"] is None


def test_the_third_milestone_claimed_closes_the_others():
    two_claimed = [claimed("mayor", by=1), claimed("gardener", by=1)]
    game = scenario(player(terraform_rating=35), player(terraform_rating=35), milestones=two_claimed)

    pick(game, "Claim the Terraformer Milestone")

    assert game.player_view(0)["milestone_cost"] is None
