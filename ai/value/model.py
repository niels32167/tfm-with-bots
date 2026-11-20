"""The Value Model: the Imitation Model's tokens and transformer (ai.imitation.model), read at the global token for
two numbers: the logit of the viewer's chance of winning, and their Victory Point margin over the other Player,
divided by MARGIN_SCALE. The margin is a secondary signal, which the spec allows to reduce the noise of a single
result per Game; only the chance of winning picks Options.

It is saved and loaded like the Imitation Model (`save_model`, `load_model(..., kind=ValueModel)`), and starts from
an Imitation Model's weights (`warm_started`): what that model learned about cards and positions is a start for
which Player is ahead.
"""

from pathlib import Path

import torch
from torch import nn

from ai.imitation.encoded import Position
from ai.imitation.model import Batch, ImitationModel, ModelShape, collate, load_model

# Victory Point margins are learned divided by this, so that the usual ones fall between about -3 and 3.
MARGIN_SCALE = 20.0
# What each of the two numbers is.
WIN, MARGIN = 0, 1


class ValueModel(ImitationModel):
    """For each position of a Batch, the logit of its viewer's chance of winning and their scaled margin."""

    def __init__(self, shape: ModelShape) -> None:
        super().__init__(shape)
        self.out = nn.Sequential(nn.LayerNorm(shape.width), nn.Linear(shape.width, 2))

    def forward(self, batch: Batch) -> torch.Tensor:
        return self.out(self.read(batch)[:, 0]).float()


def warm_started(policy: Path) -> ValueModel:
    """A Value Model with the weights of the Imitation Model saved at `policy`, except its output: a new head."""
    imitation = load_model(policy)[0]
    model = ValueModel(imitation.shape)
    weights = {name: tensor for name, tensor in imitation.state_dict().items() if not name.startswith("out.")}
    missing, unexpected = model.load_state_dict(weights, strict=False)
    assert not unexpected and all(name.startswith("out.") for name in missing), (missing, unexpected)
    return model


@torch.no_grad()
def chances_of_winning(model: ValueModel, positions: list[Position]) -> list[float]:
    """The model's chance that each position's viewer wins, on the CPU."""
    return torch.sigmoid(model(collate(positions))[:, WIN]).tolist()
