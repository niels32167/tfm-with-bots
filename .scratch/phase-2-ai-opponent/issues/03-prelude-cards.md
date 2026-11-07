# 03 — The Prelude Cards

**What to build:** All 35 Prelude Cards, working as printed. Simple effects go in the card's effect data; triggers, ongoing effects and unusual cards get Rust code (ADR 0009).

**Blocked by:** 02 — The Prelude setting and setup

**Status:** ready-for-agent

- [x] Every Prelude Card has at least one scenario test through the Python engine module, and the coverage check counts them.
- [x] Each card's own "can't pay" or "can't carry out" cases are tested.
- [x] Rules calls are in the rules notes.
- [x] Each card is playable in the GUI, and the short fuzz run stays clean with them in play.

## Comments

### 2026-11-06 — from ticket 01 (Claude)

The coverage check counts a card once it has `"effects"`, so each card needs `tests/cards/test_<id>.py` from then on. Excentric Sponsor is spelled as printed (`excentric_sponsor`). The wild Tag isn't in `Tag::COUNTED` yet. See ticket 01's Comments.

### 2026-11-07 — from ticket 02 (Claude)

26 Prelude Cards already have effect data and tests. 9 are left: Business Empire, Galilean Mining, Huge Asteroid and Aquifer Turbines ("Pay X M€": decide on Helion's heat and on a Player who can't pay, see "A Prelude Card that can't be played" in the rules notes), Acquired Space Agency and Experimental Forest (reveal until found), Ecology Experts, Excentric Sponsor, and Research Network (the wild Tag). Only Prelude Cards with effect data are dealt, so each one added changes what a Game with Prelude deals. A Scenario plays a Prelude Card with `player(prelude_cards=[...])` and `prelude=True`. See ticket 02's Comments.

### 2026-11-07 — implemented (Claude)

All 35 Prelude Cards work, and all 35 are dealt. The 9 new ones:

- **"Pay X M€" (Business Empire, Galilean Mining, Huge Asteroid, Aquifer Turbines):** the price is the card's `pay`, paid once its other effects are done (`Game::finish_prelude_card`), as an `Expense`, so Helion's heat may pay and the Player chooses how when there is more than one way. For Aquifer Turbines, what its Ocean gains for the Oceans next to it counts: a Player short of 3 is offered only the Ocean Areas that cover it. A Player who can't pay discards the card for 15 MegaCredits. The user chose this, like the open-source game.
- **Reveal until found (Acquired Space Agency, Experimental Forest):** a new `reveal` effect, `{"tag": "space", "count": 2}`, carried out once the card's other effects are done (Experimental Forest's Greenery first). The cards not taken go on the discard pile at the end, so a reshuffle in between leaves them out. The game log names each card revealed.
- **Play a card from the hand (Ecology Experts, Excentric Sponsor):** their `next_card` effect, like Special Design's and Indentured Workers', with a new `ignores_global_requirements`. Once the card's other effects are done, the Player must play a card from their hand (a new `play_card` Decision, `Waiting::CardFromHand`). They can play the Prelude Card only if a card could be played that way, judged on a copy of the Game with the Prelude Card in play, so its Tags and Production count. This copy is the engine's own, not a Controller's (ADR 0013). Otherwise they discard it for 15 MegaCredits. Playing any Prelude Card now uses up an Event's effect on the next card, as in the open-source game (`lastCardPlayed`).
- **Research Network and the wild Tag:** `Game::tags_for_an_action` adds the wild Tags to a Tag Requirement, the Builder Milestone and a card's per-Tag effects. `Game::tags` (Triggers, Awards, Victory Points) leaves them out. The user chose this, like the open-source game. The view counts the wild Tag apart (`Tag::COUNTED`), and the GUI shows it with a tooltip.

Other changes:
- The view has a new `playing_prelude_card`, which names the Prelude Card being played while its own effects are carried out (Aquifer Turbines' Ocean). It is null once they are done, as its price is paid or its card from the hand is played. The fuzz check for Ocean Areas uses it.
- Scenarios no longer check that a Prelude Card still to play is implemented; every one is.
- `to_scenario` drops a Prelude Card's effect on the card it plays, with the rest of what is under way.
- The fuzz checks allow a Prelude Card's effect on the next card while its Player plays it, and an Event's in the Prelude phase. Ecology Experts and Excentric Sponsor playing Special Design or Indentured Workers found this.
- `tests/engine/test_views.py` now matches the longest card names first in the game log, so "Mohole Area" names no Mohole.

Checks:
- **Games without Prelude unchanged:** the 120 Random Bot Games saved before ticket 02 still replay to the same view, Decision and game log, Replay JSON included. The comparison leaves out the always-empty new view keys (`playing_prelude_card`, the `wild` Tag count).
- **Tests:** 1,897 pass, the 1,000-Game fuzz run included. Clippy and fmt are clean, the GUI builds, coverage is 255/12, and the mismatch report is 0.
- **Speed:** 4 alternating rounds against efc4cbd in a scratch worktree (mains, "performance" profile): 1 process 5,477 vs 5,512 Games per second, 16 processes 55,484 vs 55,910, and Game copies 0.20 / 0.59 / 0.91 µs on both. That is under 1 %, within the rounds' noise. A first measurement showed about 2.4 %. The cause was an extra list allocated for every Action Decision's options and an extra next-card lookup for every global Requirement, and both are fixed.
- **GUI:** a Scenario played through in the browser pane with no console errors: Business Empire paid with Helion's heat in the payment picker, Ecology Experts playing Trees at -30 °C, Aquifer Turbines short of MegaCredits offered only E4 and E6, and Research Network's wild Tag on the player board. The other 5 new cards weren't tried in the browser: Excentric Sponsor uses Ecology Experts' Decision, Galilean Mining and Huge Asteroid use Business Empire's payment, and the 2 reveal cards make no Decision.

Code review (/code-review, standards and spec):
- **Fixed:**
  - the `next_card` docs (engine, view, GUI), which now also mention a Prelude Card;
  - the docs of `playing_prelude_card`, which wrongly said it lasts while the price is due; the engine field is renamed to match the view;
  - the Ocean filter, which now applies only to the Prelude Card's own Ocean, not to an Ocean bonus while it is played;
  - `megacredits_from_oceans_next_to`, now shared with the placement bonus;
  - the effects looked up once in `finish_prelude_card`;
  - a GUI `NextCardEffect` type;
  - `everything_but`, moved to the test helpers;
  - a test of Experimental Forest with too few plant cards left;
  - a bare "log", the long lines, and the test name for the view key;
  - the rules notes now say the FAQ couldn't be checked.
- **Kept, with reasons:**
  - `Player.next_card` holds an Event or a Prelude Card: the same effect type on the same card cost path, and only `to_scenario` and the fuzz checks tell them apart.
  - `tags_for_an_action` says "action" in the rulebook's sense. The one exception is a card Ecology Experts plays in the Prelude phase, which plays like an action.
  - `Tag::name` repeats the serde names, as `Resource::counted` does for Resources.
  - Copying the Game to judge Ecology Experts and Excentric Sponsor happens only for these 2 cards, at the Prelude phase's Decisions.
  - A Game described as a Scenario during a Prelude Card's payment Decision starts without that price, like any card under way (rules notes, "Scenarios with Prelude").
  - Playing a Prelude Card uses up an Event's effect on the next card. This changes no card's printed effect, and the rules notes record it.

For ticket 04: Prelude's Corporations and Project Cards are the 12 cards left. All 35 Prelude Cards are dealt, so the Prelude Card deal stays as it is. Dealing Prelude's Corporations will change the Corporation deal of Games with Prelude.
