# 05 — Milestones, Awards and final scoring

**What to build:** This ticket covers:
- **Milestones.** The five Tharsis Milestones (Terraformer, Mayor, Gardener, Builder, Planner) can be claimed as Actions.
- **Awards.** The five Tharsis Awards (Landlord, Banker, Scientist, Thermalist, Miner) can be funded as Actions.
- **Final scoring breakdown:**
  - Terraform Rating;
  - 5 per Milestone;
  - Awards: 5 for the leader and 2 for the runner-up, with ties as the rules say and no runner-up in 2-player Games;
  - 1 per Greenery;
  - 1 per Greenery next to each City, whoever owns it;
  - card Victory Points, which stay 0 until cards exist.

In the GUI, a Milestones and Awards bar shows prices and what is claimed or funded, and a final score screen shows the breakdown for each Player.

Builder, Planner and Scientist count Tags or cards in hand, so their scenario tests come in ticket 08, when hands and Tags exist.

**Blocked by:** 04 — Resources, Production and the end of the Game

**Status:** ready-for-agent

- [x] A Milestone can be claimed for 8 MegaCredits once its condition is met. Each can be claimed once, and only three per Game.
- [x] An Award can be funded for 8, 14 or 20 MegaCredits. Each can be funded once, and only three per Game.
- [x] Final scoring follows the rules, including ties and the 2-player Award rule, and the breakdown adds up to the total.
- [x] The GUI shows the Milestones and Awards bar and the final score screen.
- [x] Every Milestone and Award that doesn't depend on cards has a scenario test.

## Comments

### 2026-10-23 — implemented (Claude)

**Decisions:** The user asked Claude to make this ticket's design and rules calls without
checking with them first, so every call below is Claude's. The rules calls are in
`docs/rules-notes.md` with their sources and the tests that pin them.
- **Test seam:** the Python engine module only. The new tests are in `tests/rules/`:
  `test_milestones.py`, `test_awards.py` and `test_final_scoring.py`, plus Scenario checks in
  `test_starting_a_game.py` and a Replay round trip in `tests/engine/test_replays.py`. The
  server passes scores through unchanged. Its smoke test now finds "The Game is over." by
  content, since the log continues past it. The GUI was checked by hand in the browser.
- **Award ties follow the rulebook:**
  - everyone tied for first gets 5, and then there is no second place;
  - with one leader, everyone tied for second gets 2;
  - 2-player Games have no second place.
- **A count of 0 is scored like any other count,** following the open-source game; the
  rulebook is silent. If nobody has heat, everyone ties for first in Thermalist. With one
  leader, everyone at 0 ties for second.
- **Builder, Planner and Scientist count 0 until ticket 08.** So Builder and Planner can't
  be claimed, and a funded Scientist gives every Player 5. It is recorded as a temporary
  gap in the rules notes and pinned by a test.
- **A tie for the win** is broken by MegaCredits, as the rulebook says. Players still tied
  share the rank. Each score has a `rank` (1 is the winner) and `megacredits`, so the
  Python side never has to know the tiebreak.
- **What each one counts:**
  - Landlord counts every Tile a Player owns (Oceans belong to nobody);
  - Mayor counts Cities and Gardener Greeneries;
  - Banker compares MegaCredit Production, below zero too;
  - Thermalist and Miner count heat, and steel plus titanium, after the final Production
    phase;
  - final Greeneries count for Landlord.

**Design notes:**
- **Engine:**
  - `engine/src/milestones_and_awards.rs` holds the five Tharsis Milestones and five Awards:
    name, printed condition, a Milestone's target, and each Player's count (`count`).
    The Game keeps who claimed or funded each one in two fixed arrays
    (`claimed_milestones`, `funded_awards`), so copying a Game stays a plain value copy.
  - `Game::milestone_cost()` (8, or None once three are claimed) and `Game::award_cost()`
    (8, 14 or 20, or None once three are funded) are used both by the Options and by the view.
  - `engine/src/scoring.rs` works out final scoring:
    - the breakdown, which adds up to the total by construction;
    - each funded Award's places;
    - ranks, and how the winner won (`Win`).
  - `Board::tiles_of` and `Board::owned` count a Player's Tiles. `adjacent_oceans` became
    `adjacent(area, kind)`, so Cities can count adjacent Greeneries.
- **Decisions:**
  - Claiming and funding are Actions in the `"action"` Decision, offered only when legal.
  - Their labels read "Claim the Mayor Milestone (8 MegaCredits)" and "Fund the Landlord
    Award (14 MegaCredits)".
  - Their details are `{"type": "claim_milestone", "milestone": "mayor", "cost": 8}` and
    `{"type": "fund_award", "award": "landlord", "cost": 14}`.
  - A funding Option carries its price, since the price depends on how many are funded.
- **Scenario:** `"milestones": [{"milestone": "mayor", "claimed_by": 1}]` and
  `"awards": [{"award": "landlord", "funded_by": 0}]`. Each Milestone or Award may appear
  at most once, there are at most three of each, and the Player must exist. The test
  helpers `claimed(name, by=…)` and `funded(name, by=…)` build them, and `milestone(game,
  name)` and `award(game, name)` read them back.
- **View:**
  - The Player View lists the five Milestones (`milestone`, `name`, `condition`,
    `target`, `claimed_by`, `counts`) and the five Awards (`award`, `name`, `condition`,
    `funded_by`, `counts`).
  - It also has `milestone_cost` and `award_cost`. `counts` holds each Player's standing:
    it is public information, and play-testers need it to check Award results.
- **Scores:** `{"player", "terraform_rating", "milestones", "awards", "greeneries",
  "cities", "cards", "total", "megacredits", "rank"}`. `cards` stays 0 until cards exist.
- **Game log:** after "The Game is over.", one line per Award place, e.g. "Player 1 takes
  first place in the Landlord Award (4 Tiles) and gains 5 Victory Points." Ties read
  "shares first place". Then come each Player's Victory Points, and "Player 1 wins." (or
  "wins: tied on Victory Points, but with the most MegaCredits." or "shares the win…").
- **GUI:**
  - **The Milestones and Awards bar** (`gui/src/components/MilestonesAwards.tsx`):
    - it runs the width of the board area, under Mars and its tracks;
    - it shows the price and how many of 3 are claimed or funded;
    - for each one, it shows each Player's count in their colour, a Milestone's target,
      and who claimed or funded it;
    - the tooltip has the printed condition.
  - **Offered Milestones and Awards** are highlighted in the bar and clicked there, as
    Areas are on Mars. The status bar leaves them out and says "or click a highlighted
    Milestone or Award".
  - **Mars is sized by the window height** (`calc(100vh - 300px)`, at most 680 px), so the
    bar fits without scrolling at 1440×900.
  - **The final score screen** lists rank, the six columns of the breakdown, the total
    and MegaCredits (the tiebreak), best first, with the winner highlighted.

**Code review** (`/code-review`, standards and spec):
- Fixed:
  - the temporary Scientist, Builder and Planner gap had no rules note and no test;
  - the "What the Awards and Milestones count" note was missing its "Chosen by Claude" line;
  - added `Game::milestone_cost()` to match `award_cost()`, instead of working out the
    three-claim limit in two places;
  - the winner logic moved from `end_game` into `scoring::winners`, as one `Won` log event;
  - the Award count wording moved from a switch in `log.rs` to `Award::counted`;
  - plainer Rust in places: ranking, `award_places` and the Scenario owner check;
  - a wrong doc comment on `Place::name`;
  - the `milestone()` and `award()` test lookups moved into `tests/helpers.py`;
  - in the GUI:
    - "MC" became "MegaCredits";
    - a Player is named the same way on the face of an entry and in its tooltip;
    - the "pick on its way" flag is computed once in `App.tsx`.
- Left as is:
  - **Scenario checks.** The Milestone and Award checks in `scenario.rs` have the same
    shape, but they are short and their messages differ.
  - **The `Milestone` and `Award` enums** each repeat `ALL`, `index`, `id` and `name`, like
    `StandardProject`.
  - **The limit of three** is copied in the GUI (`PER_GAME`), like the track facts in
    `tracks.ts`.
  - **Beyond the ticket text:**
    - the per-Player `counts` in the view and the bar;
    - `rank` and `megacredits` in the scores;
    - the Award-place and winner log lines;
    - clicking Milestones and Awards in the bar instead of status-bar buttons.

    They serve play-testing and spec stories 66 and 90.
  - A claimed Milestone staying claimed has no test, because nothing can lower a count
    before cards exist.

**Open points:**
- **Ticket 08:**
  - give Builder, Planner and Scientist their real counts and add their scenario tests;
  - drop the temporary rules note;
  - add a test that a Planner stays claimed after the hand shrinks;
  - if hands make cards in hand a sensible further tiebreak, revisit the tie for the win.
- **Ticket 18:** decide whether Cities off Mars (Phobos Space Haven, Ganymede Colony)
  count for Mayor, Landlord and City scoring, and whether special Tiles count for Landlord
  (ticket 18 already says they do).
- **Ticket 21:** Helion may pay with heat as MegaCredits, which covers Milestones and Awards too.
- **Ticket 06:**
  - The fuzzer's "at most three Milestones claimed and three Awards funded" and "the score
    breakdown adds up" checks can read `milestone_cost`, `award_cost` and `scores` from the
    view.
  - Random Bots now fund Awards often (up to five Fund Options in every Action Decision),
    which changes Game length.
- **Ticket 23:** with five Players, the Terraformer counts wrap onto a second line in the bar.
