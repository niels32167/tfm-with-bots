# Card data mismatches

The printed card data imported from the fan-made card list (`engine/cards/cards.json`),
compared with the open-source game's card definitions ([terraforming-mars/terraforming-mars](https://github.com/terraforming-mars/terraforming-mars)
at commit `4d30aa07f14eeb5aa5647775ce5a7c9e49f6ac04`). Written by `uv run python -m tools.card_mismatches`; do not edit by hand.

Compared: Corporate Era, the box a card comes in, type, cost, Tags (in any order),
Requirements (in any order), Victory Points, and a Corporation's starting MegaCredits (with
what its own Trigger gives it when revealed, as Vitor's 3), for
the cards of the base box and of Prelude. The open-source game leaves the Event Tag out of
an Event card's Tags, so the comparison adds it back. Each difference is
settled by the rules authority order (rulebook, then the FryxGames FAQ, then the open-source
game), and the call is recorded in `docs/rules-notes.md`.

## Differences (0)

None.

## Not compared (1)

- #005 Search for Life: the open-source game works out its Victory Points in code

## Names that differ (0)

None.

## Names settled in the rules notes (2)

- #P01 Allied Banks: `ALLIED_BANK`
- #P11 Excentric Sponsor: `ECCENTRIC_SPONSOR`

## Missing from the open-source game (0)

None.
