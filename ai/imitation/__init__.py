"""The Imitation Model (CONTEXT.md; tickets 13 and 14 of phase 2): it predicts the Option strong Players pick at
every Decision, trained on Recorded Games.

- split.py: which Games train, which choose between models (validation) and which are held out (test).
- positions.py: the training Decisions of each Game, and batches of them encoded (ai.encoding) while training.
- model.py: the model, which scores each Option given the position, and how it is saved and loaded.
- train.py: `uv run python -m ai.imitation.train`, the training command.
- evaluate.py: `uv run python -m ai.imitation.evaluate`, accuracy on held-out Games against the baselines.
- bot.py: the Imitation Bot, the Controller that picks with the model.

Models are trained from the private dataset (.cache/recorded-games) and saved in .cache/models: out of git,
published only in the hosted Space (ADR 0014).
"""

from pathlib import Path

MODELS_FOLDER = Path(__file__).parents[2] / ".cache" / "models"
# The model the registered Imitation Bot plays with.
MODEL = MODELS_FOLDER / "imitation.pt"
# Ticket 13's model, for setup, the Draft and buying cards only, kept to play against.
DRAFT_AND_BUY_MODEL = MODELS_FOLDER / "imitation-draft-buy.pt"
