"""Prices: what things are worth in MegaCredits at a given moment, to the Player whose view they are read
from. The tests read like play, through Player Views of positions built as Scenarios."""

import tm_engine

from ai.prices import Prices


def view_of(**scenario) -> dict:
    """Player 1's view of a 2-player position, built from a Scenario."""
    scenario.setdefault("players", [{}, {}])
    return tm_engine.Game.from_scenario({"seed": 1, **scenario}).player_view(0)


OCEAN_AREAS = ["A2", "A4", "A5", "B6", "D8", "E4", "E5", "E6", "F6"]


def oceans(count: int) -> list[dict]:
    return [{"area": area, "tile": "ocean"} for area in OCEAN_AREAS[:count]]


# Mars untouched, and Mars one step short of finished.
EARLY = {"generation": 1, "temperature": -30, "oxygen": 0}
LATE = {"generation": 9, "temperature": 8, "oxygen": 14, "tiles": oceans(8)}


def test_production_is_worth_less_with_fewer_generations_left():
    early, late = Prices.of(view_of(**EARLY)), Prices.of(view_of(**LATE))

    assert early.generations_left > late.generations_left
    for resource in ("megacredits", "steel", "titanium", "plants", "energy", "heat"):
        assert early.production(resource) > late.production(resource) > 0


def test_a_victory_point_is_worth_more_near_the_end_up_to_what_a_standard_project_charges():
    early, late = Prices.of(view_of(**EARLY)), Prices.of(view_of(**LATE))

    assert early.victory_point() < late.victory_point()
    # In the last Generation a Greenery by Standard Project, 23 MegaCredits, brings 2 Victory Points
    # (its own and the Terraform Rating step), and an Asteroid brings 1 for 14.
    assert 8 <= Prices(late.view, 0, generations_left=1).victory_point() <= 14


def test_megacredits_lose_their_use_at_the_end():
    # 40 MegaCredits and only a Mine, for 4, in hand.
    view = view_of(**LATE, players=[{"resources": {"megacredits": 40}, "hand": ["mine"]}, {}])
    before, last = Prices(view, 0, generations_left=3), Prices(view, 0, generations_left=1)

    # Before the end, a MegaCredit kept is worth more than itself: spending it forgoes a later buy.
    assert before.megacredit() > 1
    # In the last Generation there is no later buy to wait for, and money no card in hand needs is
    # worth only what Standard Projects still make of it: most of the rest is lost.
    assert last.megacredit() <= 1
    board = view["players"][0]
    beyond_the_hand = (last.megacredits(40, 0, board) - last.megacredits(4, 0, board)) / 36
    assert beyond_the_hand < 0.75


def test_a_science_tag_is_worth_more_with_a_science_requirement_in_hand():
    # AI Central needs 3 science Tags.
    with_requirement = Prices.of(view_of(**EARLY, players=[{"hand": ["ai_central"]}, {}]))
    without = Prices.of(view_of(**EARLY, players=[{"hand": ["mine"]}, {}]))

    assert with_requirement.tag("science") > without.tag("science")
    assert with_requirement.tag("jovian") == without.tag("jovian")


def test_a_card_that_pays_back_is_worth_more_in_hand_early_than_late():
    # Mine: 4 MegaCredits for a steel Production step.
    early = Prices.of(view_of(**EARLY, players=[{"hand": ["mine"]}, {}]))
    late = Prices.of(view_of(**LATE, players=[{"hand": ["mine"]}, {}]))

    assert early.card_in_hand("mine") > late.card_in_hand("mine")
    assert early.card("mine") > 4 > late.card("mine")


def test_megacredits_beyond_what_the_hand_needs_are_worth_what_standard_projects_make_of_them():
    # 300 MegaCredits and nothing worth buying in hand: two copies of an early Card Economy Bot kept
    # such money rather than build Oceans, and never ended the Game.
    mid_game = {"generation": 15, "temperature": 4, "oxygen": 14, "tiles": oceans(2)}
    view = view_of(**mid_game, players=[{"resources": {"megacredits": 300}, "hand": []}, {}])
    prices = Prices.of(view)

    kept = prices.position(view, 0).parts["MegaCredits"]
    after_an_aquifer = prices.megacredits(300 - 18, 0, view["players"][0])
    assert kept - after_an_aquifer < prices.ocean()


def test_an_action_that_takes_card_resources_saved_up_is_worth_less_than_its_effect_each_generation():
    # Regolith Eaters adds a microbe each use, or removes 2 to raise the oxygen a step: a step every
    # third use.
    prices = Prices.of(view_of(**EARLY))

    played = prices.persisting_price("regolith_eaters")
    assert played < prices.step("oxygen") * prices.uses_left() / 2


def test_tag_prices_are_held_for_the_decision_though_the_hand_changes():
    # A card drawn in a Sampled Position mustn't move what a Tag in play is worth.
    # Research has 2 science Tags; AI Central and Gene Repair each need 3.
    held = {"played_cards": ["research"], "hand": ["ai_central"]}
    prices = Prices.of(view_of(**EARLY, players=[held, {}]))
    drew = view_of(**EARLY, players=[{**held, "hand": ["ai_central", "gene_repair"]}, {}])

    assert prices.position(drew, 0).parts["Tags"] == prices.position(prices.view, 0).parts["Tags"]


def test_cards_revealed_into_the_hand_are_priced_as_cards_drawn():
    # Acquired Space Agency: 6 titanium, and cards revealed until 2 with space Tags go to the hand.
    prices = Prices.of(view_of(**EARLY))

    assert prices.card("acquired_space_agency") >= 6 * prices.resource("titanium") + 2 * prices.card_drawn()


def test_a_discount_on_the_next_card_is_worth_no_more_than_a_typical_card_costs():
    # Excentric Sponsor takes 25 MegaCredits off a card, but few cards cost that much.
    prices = Prices.of(view_of(**EARLY))

    assert prices.card("excentric_sponsor") < 25 * prices.megacredit() * 0.75


def test_corporations_first_actions_and_triggers_from_their_own_code_are_priced():
    prices = Prices.of(view_of(**EARLY))

    # Valley Trust plays one of 3 Prelude Cards; Vitor funds an Award free, and gains 3 MegaCredits
    # for each card it plays with Victory Points.
    assert prices.card("valley_trust") > 37 * prices.megacredit() + 10
    assert prices.card("vitor") > 45 * prices.megacredit() + 10
    # Robinson Industries raises its lowest Production for 4 MegaCredits each Generation.
    assert prices.persisting_price("robinson_industries") > 0


def test_a_city_is_worth_less_than_its_standard_project_early_and_as_much_once_placed():
    # The published fit prices a City Tile at 9 MegaCredits in Generation 1; the Standard Project
    # charges 25 for one and a MegaCredit Production step, and Players seldom buy it so early.
    prices = Prices.of(view_of(**EARLY))
    assert 7 <= prices.city() < 25 * prices.megacredit() - prices.production("megacredits")

    # Placed on land with free neighbours, it is worth what it was before, as no Greenery came yet.
    placed = view_of(**EARLY, tiles=[{"area": "D4", "tile": "city", "owner": 0}])
    assert abs(prices.position(placed, 0).parts["Tiles"] - prices.city()) < 1
