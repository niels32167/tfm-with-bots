"""#074 Viral Enhancers (9 MegaCredits, microbe and science Tags): Effect: when you play a plant, microbe
or animal Tag, including this, gain 1 plant or add 1 Card Resource to THAT CARD."""

from tests.helpers import (
    card_resources,
    final_scores,
    greenery,
    labels,
    ocean,
    offered,
    pick,
    player,
    production,
    resources,
    scenario,
    terraformed_mars,
)


def test_its_own_microbe_tag_gains_a_plant_as_it_holds_nothing():
    game = scenario(player(megacredits=9, hand=["viral_enhancers"]), player())

    pick(game, "Play Viral Enhancers (9 MegaCredits)")

    assert resources(game, 0)["plants"] == 1
    assert card_resources(game, 0) == {}
    assert "Player 1's Viral Enhancers takes effect." in game.log
    assert game.decision["kind"] == "action"


def test_a_card_that_holds_nothing_gains_a_plant_for_each_matching_tag_without_a_decision():
    # Advanced Ecosystems is printed with an animal, a microbe and a plant Tag.
    playing = player(
        megacredits=11,
        hand=["advanced_ecosystems"],
        played_cards=["viral_enhancers", "trees", "fish", "ants"],
    )
    game = scenario(playing, player())

    pick(game, "Play Advanced Ecosystems")

    assert resources(game, 0)["plants"] == 3
    assert game.decision["kind"] == "action"


def test_other_tags_do_nothing():
    playing = player(megacredits=4, hand=["mine"], played_cards=["viral_enhancers"])
    game = scenario(playing, player())

    pick(game, "Play Mine")

    assert resources(game, 0)["plants"] == 0


def test_another_players_tags_do_nothing():
    game = scenario(
        player(megacredits=4, hand=["tardigrades"]),
        player(played_cards=["viral_enhancers"]),
    )

    pick(game, "Play Tardigrades")

    assert resources(game, 1)["plants"] == 0
    assert game.decision["kind"] == "action"


def test_a_card_that_holds_some_asks_whether_to_add_to_it_or_gain_a_plant():
    playing = player(
        megacredits=4, hand=["tardigrades"], played_cards=["viral_enhancers"]
    )
    game = scenario(playing, player())

    pick(game, "Play Tardigrades (4 MegaCredits)")

    assert game.decision["kind"] == "viral_enhancers"
    assert labels(game) == ["Add 1 microbe to Tardigrades", "Gain 1 plant"]
    assert game.decision["options"][0]["details"] == {
        "type": "viral_enhancers",
        "card": "tardigrades",
        "add": True,
    }
    assert game.decision["options"][1]["details"] == {
        "type": "viral_enhancers",
        "card": "tardigrades",
        "add": False,
    }


def test_adding_puts_the_card_resource_on_that_card():
    playing = player(
        megacredits=4, hand=["tardigrades"], played_cards=["viral_enhancers"]
    )
    game = scenario(playing, player())
    pick(game, "Play Tardigrades")

    pick(game, "Add 1 microbe to Tardigrades")

    assert card_resources(game, 0) == {"tardigrades": 1}
    assert resources(game, 0)["plants"] == 0
    assert "Player 1 adds 1 microbe to Tardigrades." in game.log
    assert game.decision["kind"] == "action"


def test_gaining_leaves_the_card_as_it_is():
    playing = player(
        megacredits=4, hand=["tardigrades"], played_cards=["viral_enhancers"]
    )
    game = scenario(playing, player())
    pick(game, "Play Tardigrades")

    pick(game, "Gain 1 plant")

    assert card_resources(game, 0) == {"tardigrades": 0}
    assert resources(game, 0)["plants"] == 1
    assert game.decision["kind"] == "action"


def test_an_animal_card_gets_an_animal():
    playing = player(megacredits=9, hand=["fish"], played_cards=["viral_enhancers"])
    game = scenario(playing, player(production={"plants": 1}), temperature=2)

    pick(game, "Play Fish")
    pick(game, "Add 1 animal to Fish")

    assert card_resources(game, 0) == {"fish": 1}


def test_it_asks_once_for_each_matching_tag_on_the_card():
    # Ecological Zone has a plant and an animal Tag, and sets itself off for each too.
    playing = player(
        megacredits=12,
        hand=["ecological_zone"],
        played_cards=["viral_enhancers"],
    )
    game = scenario(playing, player(), tiles=[greenery("C3", 0)])

    pick(game, "Play Ecological Zone")
    pick(game, area="C4")

    assert labels(game) == ["Add 1 animal to Ecological Zone", "Gain 1 plant"]
    pick(game, "Add 1 animal")
    assert labels(game) == ["Add 1 animal to Ecological Zone", "Gain 1 plant"]
    pick(game, "Gain 1 plant")
    assert card_resources(game, 0) == {"ecological_zone": 3}
    assert resources(game, 0)["plants"] == 1
    assert game.decision["kind"] == "action"


def test_it_asks_after_the_cards_taking_from_any_player():
    playing = player(megacredits=9, hand=["fish"], played_cards=["viral_enhancers"])
    game = scenario(
        playing,
        player(production={"plants": 1}),
        player(production={"plants": 1}),
        temperature=2,
    )

    pick(game, "Play Fish")

    assert game.decision["kind"] == "target"
    pick(game, "Player 3")
    assert production(game, 2)["plants"] == 0
    assert game.decision["kind"] == "viral_enhancers"


def test_with_olympus_conference_and_mars_university_their_decision_comes_first():
    # GHG Producing Bacteria's science Tag sets off those two, and its microbe Tag Viral Enhancers.
    playing = player(
        megacredits=8,
        hand=["ghg_producing_bacteria", "mine"],
        played_cards=["viral_enhancers", "olympus_conference", "mars_university"],
        card_resources={"olympus_conference": 1},
    )
    game = scenario(playing, player(), oxygen=4, deck=["trees", "comet"])

    pick(game, "Play GHG Producing Bacteria")

    assert game.decision["kind"] == "olympus_conference"
    pick(game, "Remove 1 science from Olympus Conference to draw a card")
    assert game.decision["kind"] == "discard_to_draw"
    pick(game, "Discard Mine")
    assert game.decision["kind"] == "viral_enhancers"
    pick(game, "Gain 1 plant")
    assert game.decision["kind"] == "action"
    assert resources(game, 0)["plants"] == 1


def test_a_card_resource_gain_on_decomposers_comes_as_well():
    playing = player(
        megacredits=9,
        hand=["fish"],
        played_cards=["viral_enhancers", "decomposers"],
    )
    game = scenario(playing, player(production={"plants": 1}), temperature=2)

    pick(game, "Play Fish")

    assert card_resources(game, 0)["decomposers"] == 1
    assert game.decision["kind"] == "viral_enhancers"


def test_it_does_not_set_itself_off_when_a_card_is_used_rather_than_played():
    game = scenario(player(played_cards=["viral_enhancers", "fish"]), player())

    pick(game, "Use the action of Fish")

    assert resources(game, 0)["plants"] == 0
    assert game.decision["kind"] == "action"


def test_moss_can_be_played_with_no_plant_as_its_plant_tag_gains_one_first():
    three_oceans = [ocean(area) for area in ("A2", "A4", "A5")]
    with_it = player(megacredits=4, hand=["moss"], played_cards=["viral_enhancers"])
    without = player(megacredits=4, hand=["moss"])

    assert not offered(scenario(without, player(), tiles=three_oceans), "Play Moss")
    game = scenario(with_it, player(), tiles=three_oceans)
    assert offered(game, "Play Moss")

    pick(game, "Play Moss")

    assert resources(game, 0)["plants"] == 0
    assert production(game, 0)["plants"] == 1


def test_nitrophilic_moss_can_be_played_with_1_plant_but_not_with_none():
    three_oceans = [ocean(area) for area in ("A2", "A4", "A5")]

    def playing(plants):
        return player(
            megacredits=11,
            plants=plants,
            hand=["nitrophilic_moss"],
            played_cards=["viral_enhancers"],
        )

    assert not offered(
        scenario(playing(0), player(), tiles=three_oceans), "Play Nitrophilic Moss"
    )
    game = scenario(playing(1), player(), tiles=three_oceans)
    assert offered(game, "Play Nitrophilic Moss")

    pick(game, "Play Nitrophilic Moss")

    assert resources(game, 0)["plants"] == 0
    assert production(game, 0)["plants"] == 2


def test_it_holds_no_card_resources_and_has_no_victory_points():
    played = player(played_cards=["viral_enhancers"])
    game = scenario(played, player(), **terraformed_mars())

    assert card_resources(game, 0) == {}
    assert final_scores(game)[0]["cards"] == 0
