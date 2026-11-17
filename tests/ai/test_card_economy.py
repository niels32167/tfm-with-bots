"""The Card Economy Bot compares Options by their Prices: it tries each Option one step ahead on a Sampled
Position and prices the position that follows. How strong it is is for Matches to say; these tests
check that it plays sensibly where Prices say what is right, and that it can explain a pick."""

import random

import tm_engine

from ai.card_economy import CardEconomyBot
from ai.controller import handle_for
from ai.controllers import REGISTERED, make_controller
from ai.prices import Prices
from tests.ai.test_prices import oceans

# Mid-Game, with plenty of Production: the kind of position where the first quick bot refused to
# terraform, as each step shortened its estimate of the Generations left.
MID_GAME = {"generation": 5, "temperature": -10, "oxygen": 6, "tiles": oceans(4)}
RICH = {"production": {"megacredits": 15, "steel": 3, "plants": 2}, "terraform_rating": 30}


def game_from(**scenario) -> tm_engine.Game:
    scenario.setdefault("players", [{}, {}])
    return tm_engine.Game.from_scenario({"seed": 3, **scenario})


def picked_label(game: tm_engine.Game) -> str:
    index = CardEconomyBot().pick(handle_for(game, random.Random(1)))
    return game.decision["options"][index]["label"]


def test_the_card_economy_bot_is_registered():
    assert REGISTERED["card_economy"].label == "Card Economy Bot"
    assert isinstance(make_controller("card_economy"), CardEconomyBot)


def test_terraforming_isnt_penalised_for_ending_the_game_sooner():
    game = game_from(**MID_GAME, players=[{**RICH, "resources": {"megacredits": 0, "heat": 8}}, {}])
    before = game.player_view(0)
    stepped = game.copy()
    stepped.pick(next(o["index"] for o in game.decision["options"] if o["details"]["type"] == "convert_heat"))
    after = stepped.player_view(0)

    # Estimated afresh, the step lowers the worth of all the Player has: the trap.
    assert Prices.of(after).position(after, 0).total < Prices.of(before).position(before, 0).total
    # With the estimate held for the Decision, the step is worth taking.
    assert picked_label(game) == "Convert 8 heat into a Temperature step"


def test_it_takes_the_last_step_of_the_game():
    finished_but_temperature = {"generation": 10, "temperature": 6, "oxygen": 14, "tiles": oceans(9)}
    game = game_from(**finished_but_temperature, players=[{**RICH, "resources": {"megacredits": 0, "heat": 8}}, {}])

    assert picked_label(game) == "Convert 8 heat into a Temperature step"


def explained(game: tm_engine.Game):
    return CardEconomyBot().explain(handle_for(game, random.Random(1)))


def price_of(explanation, label: str) -> float:
    return next(option.price for option in explanation.options if option.label == label)


def test_passing_keeps_what_the_player_has_though_the_generation_ends():
    # The other Player has passed, so passing ends the Action phase; the Production that follows is
    # no gain of passing's.
    game = game_from(**MID_GAME, players=[RICH, {"passed": True}])

    explanation = explained(game)

    assert price_of(explanation, "Pass") == 0


def test_it_uses_an_action_that_pays_rather_than_let_this_generations_use_go():
    # AI Central draws 2 cards each Generation; a use not taken is lost at the Generation's end.
    game = game_from(
        **MID_GAME, players=[{**RICH, "played_cards": ["ai_central"], "resources": {"megacredits": 0}}, {}]
    )

    assert picked_label(game) == "Use the action of AI Central"
