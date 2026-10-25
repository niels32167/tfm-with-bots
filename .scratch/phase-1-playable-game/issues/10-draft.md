# 10 — Draft

**What to build:** The Draft variant, on by default and switchable on the setup screen (ADR 0003).

From Generation 2, in the Research phase each Player gets 4 cards, keeps one, and passes the rest, repeating until every card is kept. The passing direction alternates by Generation as the rules say. Players then buy the cards they kept for 3 MegaCredits each.

Each Player's Player View includes the cards they passed and to whom. The GUI gets a Draft view, and the fuzzer runs with Draft both on and off.

**Blocked by:** 09 — Card flow

**Status:** ready-for-agent

- [x] Draft is on by default and can be switched off on the setup screen.
- [x] Picks and passing follow the rules for 2–5 Players, including the alternating direction.
- [x] Test: a Player View shows the cards that Player passed, and never another Player's current hand.
- [x] The GUI Draft view works in Hotseat and against Random Bots.
- [x] The fuzzer covers Draft on and off.
- [x] Every rule above has a scenario test.

## Comments

### 2026-10-25 — implemented (Claude)

**Decisions made with the user** (one round of questions; every recommended option was chosen):
- **The Draft is on everywhere by default:** `tm_engine.Game(draft=True)`, Scenarios
  (`"draft": true`), the server's `new_game` and the setup screen's new "Draft" checkbox. Tests of
  the plain Research phase pass `draft=False`. A Replay whose settings or Scenario have no `draft`
  (saved before this ticket) reads as off, as it was played.
- **A Player View keeps the cards its Player passed, and to whom, for the whole Game:** each
  player board has `passed_in_draft`, a list of `{"generation", "to", "cards"}` in the order
  passed, on the viewer's own board only (all boards in the full view).
- **The GUI extends the buying panel** rather than adding a Draft panel.

**Rules research** (the sources agree, so nothing needed the user):
- The rulebook: "Cards are passed clockwise during even-numbered generations and
  counter-clockwise during odd-numbered generations", and play proceeds clockwise. The engine's
  next Player is index + 1, so even Generations pass to index + 1. The open-source game agrees
  (`StandardDraft` passes "after" in even Generations).
- Neither source has a rule of its own for 2 Players; both directions reach the other Player.
- The rulebook has each Player simply receive the last card, and the open-source game hands it
  over automatically, so a Player holding one card keeps it without a Decision.
- No Draft at setup: "Drafting is not used during the first generation". The open-source game's
  initial draft is an optional variant of its own.

**Calls made by Claude** (recorded in `docs/rules-notes.md` under "Draft"):
- **Decision kind and Options:** kind `"draft"`, one Option per card, labelled "Keep Mine" with
  details `{"type": "draft_card", "card": "mine"}`.
- **Order:** every Player keeps one card, one at a time in player order from the first player.
  Then everyone passes the rest at the same moment, so a card passed reaches its new owner only
  once everyone has kept one.
- **When the deck and the discard pile run out during the deal:** a Player dealt fewer than 4
  still drafts. Each time, everyone holding cards keeps one, with a Decision only when they hold
  two or more, until every card is kept.
- **Game log:** "Research phase, with the Draft: each Player is dealt 4 cards, keeps one and
  passes the rest clockwise, to the next Player, until every card is kept. Then they may buy any
  of the cards they kept for 3 MegaCredits each." (counter-clockwise, "to the Player before them";
  with 2 Players, "to the other Player"), then "The Draft is over." No line names a card drafted.
- **Test seams:** the Python engine module (`tests/rules/test_draft.py`, hidden information in
  `tests/engine/test_views.py`), the fuzz invariants, and the server WebSocket for the `draft`
  setting and the Random Bot's drafting.

**Design notes:**
- **Engine:**
  - `engine/src/draft.rs` (`impl Game`) holds the Draft: `begin_draft`, `passes_clockwise`,
    `passing_to`, `begin_picking`, `can_draft`, `drafting_options`, `draft`,
    `offer_drafting_from`, `pass_drafted_cards` and `finish_draft`.
  - `Player::drafting` is a `Drafting { picking_from, kept }` of two `CardSet`s.
    `Game::draft_passes` is a `Vec<DraftPass { generation, player, to, cards }>`, the one thing
    that grows (like the log and the Replay).
  - `Phase::Draft` (view `"draft"`) comes before `Phase::Research`. `begin_research_phase` starts
    the Draft when `settings.draft` is on. `finish_draft` puts each Player's kept cards in
    `Buying::dealt`, and buying goes on as in ticket 09.
  - `Settings::draft` is `#[serde(default)]`. `Scenario::draft` defaults to true, and a Replay's
    Scenario without it reads as false (`replay.rs`).
- **View:** each player board has `drafting` (`{"picking_from", "kept", "passing_to"}`, own board
  only and only in the Draft) and `passed_in_draft` (own board only, the whole Game).
- **Server:** `new_game` takes `draft` (default true). Random Bots draft without pausing, as they
  buy (`GameSession.waiting_on_random_bot_to_draft_or_buy`), with a timed test.
- **Tests:**
  - `tests/rules/test_draft.py`:
    - the deal for 2–5 Players;
    - pick order and passing only once everyone has kept one;
    - the direction for 3–5 Players in even and odd Generations, and 2 Players;
    - the last card;
    - buying the cards kept;
    - the passed cards over two Generations;
    - the deck running out;
    - no Draft at setup;
    - the Draft off;
    - the defaults.
  - Hidden information during the Draft: `tests/engine/test_views.py`, whose check is now
    `assert_no_player_view_shows_what_others_draft_or_buy`.
  - Helpers:
    - `drafting()` and `keep_the_first_cards_offered()`;
    - `end_the_generation()` now keeps the first cards offered in the Draft;
    - `CARD_NAMES`;
    - the server's `Gui.skip_buying` became `skip_drafting_and_buying`.
- **Fuzzer:**
  - `settings_for` gains `draft`: on for seeds 0–7, 16–23 and so on, so every Player count meets
    every setting.
  - `every_card_in_exactly_one_place` counts the cards drafted from and those kept, and checks
    that only the Draft has them.
- **GUI:**
  - `BuyingPanel.tsx` now also shows the Draft:
    - the cards to keep one from, large; click one to keep it;
    - above them, small cards: those kept so far, and those passed this Generation, set by set;
    - it says whom the rest go to and whom it is waiting for;
    - the buying step after the Draft keeps the passed cards in view.
  - `cardsShownFor` replaces `buyerShown`.
  - The status bar explains the Draft, and the turn badge reads "Drafting".
  - On a player board, "Passed in the Draft (n cards)" unfolds the cards passed this Game, by
    Generation and whom they went to.
  - The setup screen has a "Draft" checkbox, on by default.
  - Checked in the browser at 1440×900:
    - against Random Bots with 3 Players, through three picks, the buying step and the
      player-board list;
    - in Hotseat with 2 Players, including Undo back over a Draft pick;
    - a new Game with the Draft off sends `"draft": false`;
    - no console errors.
- **`engine/tm_engine.pyi`** was out of date since ticket 09. It now documents the settings, the
  Draft, buying and selling Decisions, and the new view fields.
- **Game length and speed** (2026-10-24, on mains at 51 %, power-saver profile):
  - Random Bot Games average 652 picks with 2 Players (512 without the Draft), 799 with 3, 885
    with 4 and 967 with 5. The longest of 1,200 was 1,490 picks. Generations are unchanged (25
    down to 16). ADR 0004's "roughly 800 Decisions" for 2 Players with the Draft was an estimate;
    Random Bots buy and sell less than its guess.
  - Benchmark (2-player Games with the Draft): 80,046 Games/s on 16 processes and 7,240 in 1.
    Copies take 0.20, 0.60 and 0.92 µs at the start, halfway (275 picks) and at the end (551
    picks). Every target is met.
  - Fuzzing (2026-10-25, on battery at 77 %, power-saver): 20,000 Games with 2–5 Players and the
    Draft on and off, 14,693,209 Decisions in 360 s, with no failures. The longest Game lasted 40
    Generations.

**Code review** (`/code-review`, standards and spec; both reviewers were cut off once by the
session limit and resumed):
- Fixed:
  - **A Scenario saved in a Replay before this ticket** read as Draft on, unlike settings, so it
    would have gone out of step at Generation 2. `replay.rs` now reads it as off, with a test.
  - **Passing was tested only with 3 Players.** The direction test now covers 3–5 Players in
    both parities, and the 2-Player test checks where the cards go.
  - "round" (a glossary _Avoid_ word, for Generation) named the Draft's picks. They are now
    `begin_picking`, "every Player keeps one … and each picks again".
  - Docstrings and lines:
    - two lines over 120 columns;
    - missing doc comments on `draftPanel`, `buyingPanel` and `without`;
    - `drafting()`'s return type.
  - Duplication:
    - `CARD_NAMES` moved into `tests/helpers.py`;
    - the two Research-phase view tests share `research_phase_of_three_players_with_cards`.
  - `card = PROJECT_CARDS` became `cards`.
- Left as is:
  - **Names:** the buying panel keeps its name (`BuyingPanel`, `buying-panel` classes) now that it
    also shows the Draft, since the Draft is how Players choose the Research cards they buy.
  - **The kinds `"draft"` and `"buy_cards"`** are listed together in the server, the server test
    helper and the GUI, in two languages.
  - **`clockwise: bool`** in the log event, with the 2-Player wording in `log.rs`.
  - **Every new `Player` field** is set in both `Player::new` and the Scenario's struct literal,
    as before.
  - **Some tests pick by index** (`game.pick(0)`), with comments saying what is kept.
  - **Beyond the ticket text:**
    - the player-board list of passed cards, the only place the whole-Game record shows after
      the Draft (story 12);
    - the `.pyi` catch-up;
    - the server's `true_or_false` helper;
    - the reworded buying status text.

**Open points:**
- **Hidden information through sequence numbers** (from ticket 09) now also covers the Draft: a
  Decision's `sequence` counts the picks of every Player. Phase 2's encoding must leave it out.
- **Glossary:** "Draft" is in CONTEXT.md, but the parts of it used here are not: the cards
  picked from, those kept, those passed and the passing direction. Like "discard pile",
  "Research phase" and "Sell Patents", they are candidates for `/domain-modeling`.
- **Ticket 23:** the buying panel's small cards (kept and passed) are drawn at a fixed size and
  wrap onto more lines in a narrow window. They were checked only at 1440×900, not at 1024×768.
- **Ticket 24:** rerun the benchmark and the 100,000-Game fuzz with every card; Games will grow
  as more cards become playable.
- **Status line:** it stays `ready-for-agent`, because `docs/agents/triage-labels.md` has no
  "done" label.
