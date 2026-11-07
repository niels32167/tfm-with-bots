# 02 — The Prelude setting and setup

**What to build:** A Prelude setting for each Game, off by default for now, with the setup step it adds: Prelude Cards dealt, chosen and played. A few simple Prelude Cards and the 7 Project Cards' place in the deck land here, enough to play a whole Game with Prelude.

Research the rules first, in the usual order of authority (ADR 0001), and record each call in the rules notes. At least these need settling: how many are dealt and kept, when they are played and in what order, what happens when a Player can't pay for or carry out a Prelude Card, how it interacts with a Corporation's first action, and whether they count as cards played or Tags for other cards' effects. Recorded Games show 4 dealt per Player. Board Game Arena's behaviour can be checked against them, but doesn't outrank the rulebook.

**Blocked by:** 01 — Prelude cards in the catalog

**Status:** ready-for-agent

- [x] `Game` takes a `prelude` setting; it goes into Replays and Scenarios, and old Replays load as without Prelude.
- [x] Setup deals Prelude Cards and takes each choice through Decisions, hidden from other Players until the rules reveal them; the Player View test covers this.
- [x] The deck includes Prelude's Project Cards only in Games with Prelude.
- [x] The setup screen has a Prelude switch, and the GUI shows Prelude Cards while choosing and once played.
- [x] At least three Prelude Cards work end to end, each with a scenario test.
- [x] The rules notes hold every call made.
- [x] The short fuzz run also covers Prelude Games, with invariants updated (card count conserved, and so on).

## Comments

### 2026-11-06 — from ticket 01 (Claude)

Ticket 01's Comments list what this ticket must change: the deck's size and range, the `card >= PROJECT_CARDS` checks in `game.rs`, the base-box filters in `tests/helpers.py` and `StateEditor.tsx`, and `find_project_card`. A card without `"effects"` can't be played, so any Prelude card dealt here needs effect data and a scenario test.

### 2026-11-07 — implemented (Claude)

**Decisions made with the user** (one opening batch, every recommendation taken):
- **Prelude Cards now:** the 26 whose effects the existing effect data describes, each with a scenario test. Only Prelude Cards with effect data are dealt, 4 each, which 26 covers for 5 Players. Ticket 03 keeps the other 9: the four "Pay X M€" cards, Acquired Space Agency, Experimental Forest, Ecology Experts, Excentric Sponsor and Research Network.
- **Prelude's 7 Project Cards:** in the deck of a Game with Prelude now, bought and sold but never offered to play until ticket 04.
- **Seams:** the Python engine module and the server WebSocket, as before.

**Rules, all in `docs/rules-notes.md` under "Prelude"** (chosen by Claude on the user's standing instruction):
- **The rulebook** (the official Prelude rules sheet, read as a PDF from fryxgames.se) settles the deal and the timing:
  - 4 dealt and 2 kept, chosen with the Corporation and the cards bought, and keeping costs nothing;
  - played "in player order" after every Corporation is played and every card paid for (step 7b);
  - "the whole setup counts as part of generation 1";
  - they "work like green cards", Tags visible.
- **The open-source game** decides where the rulebook is silent:
  - each Player plays both before the next, in the order they choose, and the last one without a Decision;
  - a Prelude Card that can't be played is discarded for 15 MegaCredits, and doing so is not optional. A designer's ruling relayed in a forum thread and a Board Game Arena bug report say the same.
- **A Corporation's first action** comes after the Prelude Cards. Prelude Cards set off Triggers (Saturn Systems, Tharsis Republic), never CrediCor, and **Robotic Workforce** may copy their production box. The fuzzer found the last one.
- **Order of Decisions at setup:** Corporation, then 2 Prelude Cards, then buying, one Player at a time, hidden until every Player is done.

**Design notes:**
- **Engine:**
  - `Settings::prelude` and `Scenario::prelude` are written only when on, so a Game without Prelude saves byte for byte as before.
  - The new module `engine/src/prelude_cards.rs` holds the deal, keeping, playing and the 15-MegaCredit discard.
  - Each Player's `PreludeCards { dealt, kept }` uses `PreludeSet`, a `u64` of the 35 Prelude Cards, so a Player grows 16 bytes, not 80.
  - The new `Phase::PreludeCards` comes between setup and Generation 1's Action phase. `finish_unless_placing` goes on to the next Prelude Card in that phase.
  - `play_card` now ends in a shared `put_into_play`, which a Prelude Card uses too.
  - New Decisions: `prelude_cards` (Keep …) and `play_prelude_card` (Play …, or "Discard … for 15 MegaCredits (it can't be played)", with `playable` in the details).
  - The deck holds up to 215 cards, and `Deck::shuffled` takes the Game's Project Cards (`project_cards_with(prelude)`).
  - `Player::corporation` and `played_project_cards` read the new `CARDS_OF_TYPE` sets instead of `card >= PROJECT_CARDS`, and the catalog checks its own order on loading.
  - `find_project_card(id, prelude)` and `find_prelude_card` are new.
- **View:** `prelude` (public), each Player's `prelude_cards` (own view only), and `played_prelude_cards` (public).
- **Scenarios:** `prelude`, plus each Player's `prelude_cards` still to play (the Scenario then starts at that step) and `played_prelude_cards`. Without `prelude`, naming any of the Prelude box's cards is an error.
- **Server:** `new_game` takes `prelude` (default false). A Random Bot keeps Prelude Cards without pausing, as it chooses a Corporation.
- **GUI:**
  - A Prelude switch on the setup screen, with a note that Prelude is unfinished.
  - The buying panel shows the Prelude Cards to keep from next while a Player chooses a Corporation, then the 4 dealt, with "Kept" on those kept.
  - The kept Prelude Cards show "hidden for now" above the cards to buy, then the panel offers them to play, with a ribbon on one that can't be played.
  - New status-bar texts, a "Prelude Cards" turn badge, and a Prelude Cards column on each player area.
  - The state editor offers Prelude's Project Cards in a Scenario with Prelude.
- **Fuzzer:** `settings_for` turns Prelude on for seeds 8–15 of every 16, so every Player count meets every mix of Draft and Prelude. `cards_in_play` counts played Prelude Cards. `every_card_in_exactly_one_place` uses the Game's own Project Cards. A new invariant, `prelude_cards_stay_hidden_until_played`, comes with its own tests.

**Checks:**
- **Games without Prelude unchanged:** 120 Random Bot Games (2–5 Players, Draft and Corporations on and off; 80,927 picks) were saved from d0f57aa before any engine change. With this build, each Replay replays to the same full view, Decision and game log, the same seeds play the same Games, and the Replay JSON is identical. The comparison leaves out the view's three new keys (`prelude`, `prelude_cards`, `played_prelude_cards`), which are always false, null and empty in such a Game. The throwaway script was in the session scratchpad. The suite's own guards are `tests/rules/test_games_without_prelude.py`, the Replay tests and `test_a_replay_saved_before_prelude_existed_plays_without_it`.
- **Speed** (4 alternating rounds of `tools.benchmark --seconds 6` against d0f57aa in a scratch worktree, since removed; on mains power, "performance" profile):
  - 1 process: 5,391 Games per second against 5,381 (+0.2 %);
  - 16 processes: 55,184 against 54,667 (+0.9 %);
  - The rounds overlap, so there is no slowdown. Copies: 0.20 / 0.59 / 0.89 µs against 0.20 / 0.58 / 0.91.
- **Browser** (1440×900): a Prelude Game on seed 7 against a Random Bot, through choosing CrediCor, keeping 2 of 4, buying, the bot's Prelude Cards and mine (the second played without a Decision) into Generation 1. A Scenario loaded over a second WebSocket showed the ribbon on a Loan that can't be played. No console errors.
- **Full run:** 1,854 tests, including the 1,000-Game fuzz run with Prelude Games. Also clippy, `cargo fmt --check`, the GUI build, the coverage check (246 implemented cards tested, 21 not implemented) and the mismatch report (0 differences).

**Code review** (`/code-review`, standards and spec):
- Fixed:
  - Glossary: "Preludes" for the cards became `Phase::PreludeCards` / `"prelude_cards"`, the module `prelude_cards.rs`, `prelude_card_ids`, and the GUI column key. README now says "the Prelude box's 47 cards". A test name lost "step".
  - Lines over 120 columns in 10 card test docstrings and 3 tests.
  - `offer_keeping_prelude_card` returned an unused bool. `discard_prelude_cards_not_kept` is now `put_back_…`, as they go back in the box. `isBought` became `isMarked`, and the play button's aria-label no longer assumes every ribbon means "Discard".
  - The catalog-order check became a plain if/else.
  - Spec review: the shuffle order and the 215-card deck, and a hand-off on "Pay X M€" cards, are now in the rules notes.
- Left as is:
  - The GUI's `keepingPreludeCards` mirrors the engine's `keeping_due`, since the GUI can only read the view.
  - Rules numbers (2 kept, 15 MegaCredits) are written in the GUI text.
  - The lists of Decision kinds in `cardsShownFor`, `PICKED_IN_THE_PANEL`, the server and `skip_buying` grow with each new kind. That pattern predates this ticket.
  - `prelude: bool` is threaded through the Scenario's helpers.
  - The Robotic Workforce call goes beyond the ticket, but play reaches it as soon as Prelude Cards are dealt.

**Open points:**
- **Replays of Prelude Games:** while Prelude is unfinished, each ticket that gives more cards effect data changes what a Game with Prelude deals or offers. Such Replays may stop loading until ticket 05. The setup screen says so.
- **Ticket 03:**
  - the 9 remaining Prelude Cards;
  - "Pay X M€" with Helion's heat, and paying when the Player can't (the 15-MegaCredit discard);
  - the wild Tag (`Tag::COUNTED`, `CountedTag`, `COUNTED_TAGS`);
  - each card's own "can't carry out" cases.
- **Ticket 04:**
  - Prelude's 5 Corporations aren't dealt, and `find_corporation` still means the base box;
  - Valley Trust's first action draws Prelude Cards, but the Prelude Cards not dealt aren't kept anywhere yet. A Prelude deck in `Game` could hold them, which changes Prelude Games' draws only.
  - `CARDS_HOLDING_CARD_RESOURCES` and Psychrophiles, as ticket 01 noted.
- **Ticket 05:** Prelude on by default, and the benchmark with it on.
- **State editor:** it can't yet put Prelude Cards in a Scenario. Scenario files with them load fine.
- **The user:** if you have the box, check how Allied Banks and Biolab are printed (from ticket 01).
