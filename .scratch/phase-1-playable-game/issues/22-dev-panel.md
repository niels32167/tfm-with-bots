# 22 — Dev panel

**What to build:** A panel for hunting rule bugs, toggled on and off over the game view. It has:
- the seed;
- the full game log;
- Replay step-through, forwards and backwards;
- a full-view switch showing all hands and the deck order;
- a state editor.

With the state editor, the user can give a Player Resources or Production, set Global Parameters, put specific cards in a hand or among played cards, place a Tile, and set the Generation. An edited state is a Scenario, saved and loaded like any Replay, so a setup found in the GUI can become an automated test.

**Blocked by:** 02 — New Game setup, seed, undo and Replays; 08 — Playing Project Cards

**Status:** ready-for-agent

- [x] The panel can be toggled without disturbing the Game.
- [x] Replay step-through moves forwards and backwards and shows the state at each step.
- [x] The full-view switch shows all hands and the deck order.
- [x] Each kind of state edit above works and produces a Scenario that can be saved and reloaded.
- [x] A saved Scenario can be used directly in a scenario test.

## Comments

### 2026-10-29 — notes from tickets 11 and 12 (Claude)

- **Scenarios refuse** a Greenery on an Area reserved for Oceans and an Ocean on land, so they
  can't yet describe a position after Mangrove (ticket 11) or Artificial Lake (ticket 12). The
  state editor will need them: allow one per card played that puts one there (Oceans belong to
  nobody, so one Ocean on land per Artificial Lake played by anyone).
- **Scenarios don't check** that Cities keep apart, so they accept a position after Urbanized Area
  (ticket 12), but also Cities next to each other that no rule allows. The fuzzer's
  `tiles_only_on_legal_areas` says what is legal, and the state editor could reuse its rules.

### 2026-11-01 — notes from ticket 18 (Claude)

- **Scenarios now describe special Tiles and Land Claim**: `{"area": "C4", "tile": "special",
  "card": "nuclear_zone", "owner": 0}` (Capital's is a `"city"` with `"card": "capital"`), a City on
  an Area reserved for a card's City, Mohole Area's Tile on an Area reserved for Oceans, and
  `"land_claim": {"area": "C3", "player": 1}`. They don't check that the Tile's card was played, or
  where a special Tile's card allows it (Lava Flows on a volcano, and so on); the fuzzer's
  `special_tiles_where_their_cards_put_them` and `each_reserved_area_used_only_by_its_card` say
  what is legal, and the state editor could reuse them.

### 2026-11-04 — hand-off from ticket 19 (Claude)

Scenarios now take a Player's `"card_resources"`, such as `{"tardigrades": 3}`: the state editor should let the user set them on played cards that hold some (`effects.holds` in the catalog). The Scenario refuses them on a card not played or holding none.

### 2026-11-05 — hand-off from ticket 21 (Claude)

Scenarios now take a Player's `"corporation"`, revealed and giving no starting values, and `"first_action_due"`. The state editor should let the user set both (only Inventrix and Tharsis Republic have a first action). A Scenario can't yet say that a Terraform Rating was raised this Generation (`terraform_rating_raised`, which United Nations Mars Initiative's action needs), nor which actions were used, so a position mid-Generation starts with neither.

### 2026-11-06 — implemented (Claude)

**Decisions made with the user:** none. The calls were to be made without a question batch, as on tickets 19 to 21, so every call below is Claude's recommended one, recorded in `docs/rules-notes.md` ("A Tile only a card puts there", "What a Scenario doesn't refuse", "A position in the middle of a Generation") as chosen on the user's instruction.

**Calls made by Claude:**
- **Positions real play can't reach are listed, not refused.** The Comments said the state editor "could reuse" the fuzzer's rules. A Scenario still accepts Cities next to each other and the like, as refusing would break Replays and tests holding such positions (ADR 0010), and a bug hunter may want one. The panel shows them under "Real play can't reach this position".
- **The server imports `tests.fuzzing.invariants`** (`tiles_only_on_legal_areas`, `special_tiles_where_their_cards_put_them`, `each_reserved_area_used_only_by_its_card`), so they stay the one place that says what is legal. It is the only import from the server into `tests/`; nothing is packaged, and `tests/fuzzing/invariants.py` imports nothing of the server.
- **All of ticket 21's open fields were added, and more:** `terraform_rating_raised` and `used_actions`, as the hand-off asked, and `passed`, `next_card`, `current_player` and `actions_this_turn`, since otherwise editing one number in the middle of a Generation gives Turns back to Players who passed.
- **A Scenario starts at an Action.** Reading a position in the middle of a compound Action or outside the Action phase drops what is under way, and those cards go into the deck beneath the cards it names; the editor says so.
- **Looking back honours the full-view switch:** with it off and one human, a step shows that Player's Player View, and another Player's Options stay hidden. The state editor holds every hand regardless, since a Scenario does.
- **Starting from a position replaces the Game, with no undo back:** save a Replay first to keep it. Random Bots keep playing while someone looks back.
- **Milestones, Awards, the deck order and the discard pile are kept, not edited:** the ticket doesn't list them, and they are in the file. A card put in a hand or among played cards leaves wherever it was, deck included; one taken out goes beneath the deck's named cards.

**Design notes:**
- **Engine:** `Game::to_scenario` in `scenario.rs` writes all `Scenario` fields in one struct literal, so a new field can't be forgotten. `AllowedByCards` counts what the played cards' `"tiles"` allow, so a new card needs no change. `Start::Scenario` now holds a `Box`, which clippy asked for as `Scenario` grew. Nothing here is on the path of a Random Bot pick.
- **Server:** one read-only message, `dev_view`, answered only to the GUI that asked, with the step (one beyond the end means the latest), `view` as the screen shows it, `full_view`, the Decision and index picked, the log, the position as a `scenario` and `position_problems`. An earlier step is a Game from `Game.from_replay`, so the Game itself is never touched. The state editor starts a Game with the existing `load_replay`, so a Scenario saves and loads like any Replay.
- **GUI:** `DevPanel.tsx` (seed, switch, step-through, Decision at the step, hands and deck, log), `StateEditor.tsx`, and `scenario.ts` for its edits. `App` overlays the step's view on the update, so the board, tracks, player boards, hand and played cards all show it with no change of their own; nothing can be picked while looking back. `.game` makes room for the panel, so nothing is covered. Closing the panel leaves the Player View. Every kind of edit went through the browser; `scenario.ts` has no automated test, as the GUI has no test runner.
- **`load_game(path)`** in `tests/helpers.py` starts a scenario test from a saved file. `Game.from_scenario(file["replay"]["start"]["scenario"])` works too.
- **Tests** (1,708 in all, up from 1,652): `tests/rules/test_scenarios.py`, including that at every "action" Decision of random Games with 2, 3 and 5 Players, a position described as a Scenario starts the same full view and Options, and that every position of a Game can be described; `tests/server/test_dev_panel.py`, including one test per kind of edit that saves, reloads and runs through `load_game`.
- **Checked in the browser** (1440×900, a human against a Random Bot, Scenarios and Replays through a second WebSocket): toggling leaves the boards and status bar as they were; First, Back, Forward, Latest and the slider show each step, its Decision, the Option picked and the log; a step's Player View with the switch off; the full view with all hands and 172 cards of deck in order, and the human can still pick; every kind of edit; two Cities and a Land Claim listed as unreachable; save and reload giving the same boards; a refused Ocean on land staying on screen past a later update, with the Game unchanged; Enter in a number field starting nothing; loading another Game while looking back returns to the Game's Decision. No console errors, but for one failed WebSocket retry while the server was restarting.
- **Game length and speed** (2026-11-06, on battery, "performance" profile):
  - Fuzzing: 20,000 Games with 2–5 Players and 13,166,167 Decisions in 346 s, on the final engine, clean, the longest Game 33 Generations. An earlier run before the review's fixes was clean too (13,180,947 Decisions).
  - Benchmark: 5,440 Games/s in 1 process and 55,543 on 16. A copy takes 0.19 to 0.87 µs. Every target met.
  - Three rounds alternating with 0c7d2c8 (6 s each): this engine 5,493, 5,563 and 5,520 Games/s in 1 process, and 55,782, 55,547 and 55,603 on 16; 0c7d2c8 5,384, 5,475 and 5,514, and 56,081, 56,214 and 55,821. No measurable change: within what identical runs differ by.
- **Card mismatch report:** 0 differences.

**Code review** (`/code-review`, standards and spec):
- Fixed:
  - A step that no longer exists, after a new Game, a load or an undo, hid the human's Decision behind "Looking back at step 0 of 0".
  - Edits survived loading another Game and could replace it with the old position; the editor now says which step it read from.
  - Looking back ignored the full-view switch in a one-human Game: `dev_view` now has `view` and `full_view`.
  - Enter in a field started the Game, as the editor was a form.
  - Handing United Nations Mars Initiative to another Player left its used action behind, which the engine refused.
  - A refusal vanished at the next update, so the panel keeps it until the next try.
  - The word "draft" for an edited position (`edited` now), "move" in names (`putCard`), and `while` loops without `MAX_PICKS`.
  - Comments the change made false (`first_player`, the `.pyi` on where cards are named), a comment left away from its code, and duplicated Resource names, track numbers and Player lists in the editor. Rules notes name their tests.
  - Found in the browser: the panel's tabs shrank to nothing, and the small cards above the Corporations ran over the player boards at this width, so they wrap now.
- Left as is:
  - **The server importing the invariants from `tests/`:** see above. Moving them out would be churn for a local tool.
  - **In the full view with one human, the buying panel hides while another Player decides:** `cardsShownFor` follows the Decision there, as in Hotseat; the hand and the panel's lists still show the cards.
  - **`tileFrom(kind: string, ...)`, and the `edited, onChange` props that travel together:** a type or bundle reads no better in so small a form.
  - **`Game::describe(player, in_action_phase)` reads mostly `player`:** it needs the Game's Card Resources too.
  - **The extra fields beyond the hand-off, and the editor's Terraform Rating, first player, whose Turn, passed and next card:** unasked but needed for an exact position, and cheap.

**Open points:**
- **Hand-offs:** ticket 25 (how to use the panel for a bug found in play).
- **Still open from earlier tickets:** the paw's emoji font (ticket 23), the 100,000-Game run and `implemented_cards_first` (ticket 24).
- **Status line:** it stays `ready-for-agent`, because `docs/agents/triage-labels.md` has no "done" label.
