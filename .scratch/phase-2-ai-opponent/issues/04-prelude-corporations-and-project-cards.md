# 04 — Prelude's Corporations and Project Cards

**What to build:** Prelude's 5 Corporations (Cheung Shing Mars, Point Luna, Robinson Industries, Valley Trust, Vitor) and 7 Project Cards (House Printing, Lava Tube Settlement, Martian Survey, Psychrophiles, Research Coordination, SF Memorial, Space Hotels), working as printed.

Valley Trust's first action draws on Prelude Cards, so it depends on the setup step. Decide whether the Corporations are dealt only in Games with Prelude; Recorded Games show all 17 together in those Games.

**Blocked by:** 02 — The Prelude setting and setup

**Status:** ready-for-agent

- [x] Each card and Corporation has at least one scenario test, and the coverage check counts them.
- [x] Rules calls are in the rules notes.
- [x] Each is playable in the GUI, and the Corporations show on the player board with their abilities.
- [x] The short fuzz run stays clean with them in play.

## Comments

### 2026-11-06 — from ticket 01 (Claude)

The coverage check counts a card once it has `"effects"`. The mismatch report compares a Corporation's starting MegaCredits once it has effect data, and Vitor will then differ: 45 as printed, 48 in the open-source game, which adds its own effect's 3. Psychrophiles may need `CARDS_HOLDING_CARD_RESOURCES` raised. See ticket 01's Comments.

### 2026-11-07 — from ticket 02 (Claude)

Prelude's 7 Project Cards are in the deck of a Game with Prelude, unplayable until they get effect data, and a Scenario with `prelude=True` may name them. Prelude's Corporations aren't dealt and `find_corporation` still means the base box. For Valley Trust, the Prelude Cards not dealt aren't kept anywhere yet. See ticket 02's Comments.

### 2026-11-07 — implemented (Claude)

All 12 work: Prelude's 7 Project Cards and 5 Corporations. Every card in the catalog now has effect data and a scenario
test: the coverage check reports 267 implemented, 0 left.

**Decisions made with the user** (one opening batch, every recommendation taken):
- **Seams:** the Python engine module, as before. No server change was needed: the new Decisions reach the GUI as
  before (`free_award`, and `play_prelude_card` in the Action phase).
- **Prelude's Corporations** are dealt only in Games with Prelude, from all 17. A Game without Prelude deals and draws
  exactly as before.
- **Vitor counts itself:** it starts with the printed 45 and gains 3 once revealed ("including this"), as in the
  open-source game. The mismatch report counts a Corporation's Trigger set off by itself in its starting MegaCredits,
  so it shows 0 differences.
- **Discounts per Tag:** Cheung Shing Mars and Valley Trust take 2 off for each building or science Tag, so Research
  costs 4 less with Valley Trust.

**Rules calls by Claude**, all in `docs/rules-notes.md` under "Prelude", each saying the FAQ couldn't be checked:
- **Robinson Industries:** compares all six Productions as they are, so MegaCredit Production below 0 is the lowest.
  It asks only when several are tied.
- **Vitor:**
  - a card's Victory Point icon counts if it is 0 or more, points per something included (Tardigrades), and Events
    count too;
  - the free Award counts as funded, and with 3 Awards funded Vitor goes without its first action.
- **Valley Trust:**
  - the Prelude deck is the Prelude Cards nobody was dealt, not those discarded at setup;
  - 3 are drawn at random from it, as from a shuffled deck, and only their Player sees them;
  - the one picked is played as at setup (price, Tiles, card from the hand), and one that can't be played is offered
    as "Discard … for 15 MegaCredits";
  - the other 2 are discarded unseen, and the Action ends once the Prelude Card is done.
- **Point Luna:** draws for its own Earth Tag when revealed, and for an Event's.
- **Psychrophiles:** microbes pay 2 each towards a card with a plant Tag. As with steel, a way to pay with a microbe
  the others make unneeded is left out.
- **Lava Tube Settlement:** its City goes on any free volcano, as Lava Flows' Tile does.

**Design notes:**
- **Effect data:** a Trigger may `draw` (Point Luna), and a new Trigger condition, `card_with_victory_points` (Vitor),
  counts the Corporation itself. A discount may be `per_tag`. A first action may `fund_award` (Vitor) or draw
  `prelude_cards` (Valley Trust).
- **Psychrophiles:** `Payment` has `microbes`, which `ways_to_pay` splits like the cubes, and paying takes them off the
  card. The Player View leaves `microbes` out of an Option's details while it is 0, so a Game without Prelude shows its
  Options as before. `CARDS_HOLDING_CARD_RESOURCES` is 19.
- **Robinson Industries** is Rust code (`card_code::ROBINSON_INDUSTRIES`, `Game::lowest_productions`): its action is a
  Production change, `ProductionChange::RaiseLowest`, through the same Decision as a card's.
- **Vitor:** the new `Waiting::FreeAward` offers the usual `FundAward` Options at cost 0.
- **The Prelude deck:**
  - `Game::prelude_deck` is a `PreludeSet` (8 bytes, ADR 0004), and the view shows `prelude_deck_size`;
  - the drawn cards go into the Player's `prelude_cards.kept`, so the setup's playing code runs unchanged:
    `Waiting::DrawnPreludeCards`, then `play_prelude_card`, which discards the rest;
  - `play_next_prelude_card` ends the Action outside the Prelude phase, and `finish_unless_placing` finishes a Prelude
    Card under way in the Action phase.
- **Scenarios:**
  - may name Prelude's Corporations, and `prelude_deck` (left out, every Prelude Card named nowhere else);
  - `to_scenario` writes the Prelude deck. Mid-draw, it puts the drawn cards back and leaves the first action due, so
    the Scenario starts before it.
- **GUI:**
  - the payment picker has a microbe stepper;
  - the buying panel shows the drawn Prelude Cards ("First action: your 3 Prelude Cards drawn");
  - new status-bar texts for the free Award and the drawn Prelude Cards;
  - the player board shows a Corporation's first action while it is due;
  - the setup hint no longer calls Prelude unfinished.
- **The user's GUI note:** two played Prelude Cards stacked exactly on top of each other, as a Prelude Card is shorter
  than a Project Card. The Prelude Cards column now overlaps them less, so each title shows.
- **Fuzz checks:** they know Prelude's Corporations, the per-Tag discounts, microbe payments, Lava Tube Settlement's
  City next to others, and Valley Trust's draw: 3 Prelude Cards held in the Action phase, and up to 3 played. Each
  comes with a test in `tests/fuzzing/test_invariants.py`.
- **Glossary:** "Prelude deck" is in CONTEXT.md.
- Ticket 01's request is done here, as every card has effect data: `test_every_card_is_implemented` covers the whole
  catalog, and the coverage check's exception for the Prelude box is gone.

**Checks:**
- **Tests:** 1,960 pass, the 1,000-Game fuzz run included, with no fuzz failures. Clippy and fmt are clean, the GUI
  builds, coverage is 267/0, and the mismatch report is 0.
- **Games without Prelude unchanged:** the 120 Random Bot Games saved before ticket 02 (2–5 Players, Draft and
  Corporations on and off; 80,927 picks) still replay to the same view, Decision and game log, the same seeds play the
  same Games, and the Replay JSON is identical. The comparison also leaves out the new `prelude_deck_size`, always 0
  in such a Game. Checked at c040294 before any change, and again after the code review's fixes.
- **Speed:** 4 alternating rounds of `tools.benchmark --seconds 6` against c040294 in a scratch worktree, since
  removed (mains, "performance" profile):
  - 1 process: 5,543 Games per second against 5,595 (−0.9 %), the rounds going both ways (−0.3, +0.4, −1.3, −2.4 %).
  - 16 processes: 55,277 against 55,208 (+0.1 %).
  - Game copies: 0.22 / 0.61 / 0.93 µs against 0.20 / 0.60 / 0.90.
  - A first measurement, taken while the code review ran, showed 3.8 % slower with 1 process. `can_play` now asks
    whether Psychrophiles is in play before reading the card's Tags, as it does this for every card in hand at every
    Action Decision.
- **GUI (browser pane, 1440×900, no console errors):** a Scenario showing:
  - both played Prelude Cards with their titles;
  - Valley Trust's first action drawing Business Empire, Ecology Experts and Loan, with Loan marked "can't be
    played";
  - Ecology Experts playing Trees at -30 °C, paid with 9 MegaCredits and 2 microbes from Psychrophiles;
  - Vitor's first action funding the Miner Award for free;
  - Robinson Industries' action raising titanium Production, the only lowest;
  - each Corporation on its player board with its ability, and its first action while due.

**Code review** (`/code-review`, standards and spec):
- **Fixed:**
  - a stale doc on `change_production_as_chosen`;
  - Robinson's action now uses `choose_production_change` instead of repeating it;
  - the hand-built plural in the game log's "draws 3 Prelude Cards", now `counted`;
  - a second `is_zero`;
  - comments over 110 columns and lines over 120 in the tests, the fuzz checks and the buying panel;
  - a comment in `tools/card_mismatches.py` that sat above the wrong constant;
  - `to_scenario`'s filter on a constant;
  - the fuzz check for a Prelude Card's effect on the next card is narrowed to Valley Trust's Player;
  - "Prelude deck" added to the glossary;
  - the player board now shows a Corporation's first action;
  - a Game described mid-draw keeps Valley Trust's first action due.
- **Kept, with reasons:**
  - `ways_to_pay` takes six numbers, two of them 0 for expenses and actions. Only three callers use it, and bundling
    them would change every caller for one new part.
  - The drawn Prelude Cards share `prelude_cards.kept` with those kept at setup. It is what a Player has still to play,
    and it lets the setup's play code, view and GUI panel serve Valley Trust unchanged. The cost is the Action-phase
    special cases in the fuzz check and the GUI.
  - The first-action kinds are checked in three places (whether it can be taken, taking it, its label), as Inventrix's
    and Tharsis Republic's were.
  - The log-and-draw pair now appears in three places. It is two lines each time.
  - `PSYCHROPHILES` and `ROBINSON_INDUSTRIES` are offsets into the Prelude box, which the catalog checks against their
    ids on loading, as for every card with code.
  - `prelude_deck_size` in the view: the fuzz check uses it to tell whether Valley Trust can take its first action.

**Open points:**
- A Replay of a Game with Prelude saved before this ticket may not load: Prelude's Corporations now join the deal.
- **Answered by the user (2026-11-07):** the printed cards say Allied Banks and Biolabs. Biolab is now Biolabs (id
  `biolabs`): the card import corrects the card list's spelling, the mismatch report lists it as settled, and the
  rules notes say the user checked both. A Scenario file naming `biolab` no longer loads.

