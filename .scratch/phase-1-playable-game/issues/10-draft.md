# 10 — Draft

**What to build:** The Draft variant, on by default and switchable on the setup screen (ADR 0003).

From Generation 2, in the Research phase each Player gets 4 cards, keeps one, and passes the rest, repeating until every card is kept. The passing direction alternates by Generation as the rules say. Players then buy the cards they kept for 3 MegaCredits each.

Each Player's Player View includes the cards they passed and to whom. The GUI gets a Draft view, and the fuzzer runs with Draft both on and off.

**Blocked by:** 09 — Card flow

**Status:** ready-for-agent

- [ ] Draft is on by default and can be switched off on the setup screen.
- [ ] Picks and passing follow the rules for 2–5 Players, including the alternating direction.
- [ ] Test: a Player View shows the cards that Player passed, and never another Player's current hand.
- [ ] The GUI Draft view works in Hotseat and against Random Bots.
- [ ] The fuzzer covers Draft on and off.
- [ ] Every rule above has a scenario test.
