# 09 — Card flow: setup buy, Research phase, Sell Patents

**What to build:** How cards move through a Game:
- **Setup.** Each Player is dealt 10 Project Cards and buys any of them for 3 MegaCredits each. Starting MegaCredits stay at the temporary fixed amount until Corporations arrive in ticket 21.
- **Research phase.** From Generation 2 onwards, each Player draws 4 cards and buys any of them for 3 each; the rest are discarded.
- **Hidden choices.** Buying is done one Player at a time in player order (ADR 0002) and stays hidden from the other Players.
- **Sell Patents.** The Standard Project lets a Player pick cards one at a time, then "done", for 1 MegaCredit each.
- **Reshuffle.** When the deck runs out, the discard pile is reshuffled into a new deck.
- **Player View.** It never contains another Player's hand or the deck order.

The GUI gets the buying screens and Sell Patents.

**Blocked by:** 08 — Playing Project Cards

**Status:** ready-for-agent

- [ ] The setup buy and the Research phase work for 2–5 Players and appear in the GUI.
- [ ] Test: during buying, no Player View contains another Player's hand, choices or the deck order.
- [ ] Sell Patents works as a chain of single picks ending with "done".
- [ ] Test: the deck reshuffles from the discard pile when it is empty.
- [ ] The fuzzer gains a card-count invariant: deck, discard pile, hands and played cards always add up to the full card set.
- [ ] Every rule above has a scenario test.
