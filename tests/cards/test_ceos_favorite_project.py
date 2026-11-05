"""#149 CEO's Favorite Project (1 MegaCredit, Event Tag): add 1 Card Resource to a card with at least
1 on it."""

from tests.helpers import card_resources, labels, offered, pick, player, scenario


def test_it_cannot_be_played_without_a_card_of_the_players_with_a_card_resource_on_it():
    empty = player(
        megacredits=1, hand=["ceos_favorite_project"], played_cards=["tardigrades"]
    )
    holding = player(played_cards=["ants"], card_resources={"ants": 3})

    assert not offered(scenario(empty, holding), "Play CEO's Favorite Project")


def test_it_adds_1_to_the_only_card_with_some_without_a_decision():
    playing = player(
        megacredits=1,
        hand=["ceos_favorite_project"],
        played_cards=["tardigrades", "regolith_eaters"],
        card_resources={"tardigrades": 2},
    )
    game = scenario(playing, player())

    pick(game, "Play CEO's Favorite Project (1 MegaCredit)")

    assert card_resources(game, 0) == {"regolith_eaters": 0, "tardigrades": 3}
    assert game.decision["kind"] == "action"


def test_it_can_target_animal_and_fighter_cards():
    playing = player(
        megacredits=1,
        hand=["ceos_favorite_project"],
        played_cards=["security_fleet", "fish", "birds"],
        card_resources={"security_fleet": 1, "fish": 2},
    )
    game = scenario(playing, player())

    pick(game, "Play CEO's Favorite Project")

    assert labels(game) == ["Add 1 fighter to Security Fleet", "Add 1 animal to Fish"]
    pick(game, "Add 1 animal to Fish")
    assert card_resources(game, 0) == {"birds": 0, "fish": 3, "security_fleet": 1}


def test_it_can_add_any_kind_of_card_resource_and_the_player_picks_the_card():
    playing = player(
        megacredits=1,
        hand=["ceos_favorite_project"],
        played_cards=["tardigrades", "physics_complex", "regolith_eaters"],
        card_resources={"tardigrades": 1, "physics_complex": 2},
    )
    game = scenario(playing, player())

    pick(game, "Play CEO's Favorite Project")

    assert labels(game) == [
        "Add 1 microbe to Tardigrades",
        "Add 1 science to Physics Complex",
    ]
    pick(game, "Add 1 science to Physics Complex")
    assert card_resources(game, 0) == {
        "physics_complex": 3,
        "regolith_eaters": 0,
        "tardigrades": 1,
    }
