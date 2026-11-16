# 10 — Recorded Games in the engine

**What to build:** Replay Recorded Games through the engine: the cards dealt and drawn taken from the log, and each move matched to one of the Options offered. This gives two things:

1. **Action-phase training data.** Each Decision then has the engine's own Options and Player View, the same inputs a trained Controller sees in play, with the Player's real pick marked.
2. **A test of the rules on real play.** Where the engine refuses a move or disagrees about the result, either we have a bug or Board Game Arena has its own ruling.

It needs a way to start a Game with a chosen deal and draw order; find the smallest change to the engine or Scenario that allows it, since a Scenario currently starts in the Action phase. Compare trackers after each move, and stop that Game at its first difference, so that one difference doesn't cascade.

Expect many differences at first, mostly from parsing. Group them by cause and work down the largest groups. Stop when what remains is rare or isn't worth chasing, and record the decision.

**From ticket 09:**
- **Hands.** Take them from `ai.recorded_games.hands.HandReader` with `resync=True`. Replay first the 42,431 "named" Games, whose versions name both Players' cards; ticket 09's Comments say how to recognise them.
- **Sold cards.** Sell Patents and Mars University discards never name their cards. Choose them in hindsight from the named cards in hand that the Player never plays later. Any such choice replays the same; it is possible for 99% of Players.
- **Cards that entered unnamed** take their names from their plays.
- **Parser differences, not engine bugs:** a play `HandReader` finds "missing" (0.57%), a Hand Counter mismatch at a fresh check, or an `unread` line (a renamed account, 710 Games).

**Blocked by:** 05 — Prelude exit checks; 09 — Find what the hand rebuild misses

**Status:** ready-for-agent

- [x] One command replays a sample or all suitable Games on all cores, and reports the share that replay fully, how far the others get, and differences grouped by cause.
- [x] Each difference group is called parser, engine bug, or Board Game Arena's ruling. Engine bugs get a regression test and the usual rules note; rulings get a rules note saying why the rulebook stands.
- [x] The share of Games replayed fully, and how many that gives at each rating, is recorded under Comments. A Game that replays partly can still give the Decisions before its first difference, and the dataset says so.
- [x] The dataset gains Action-phase Decisions with Options and the pick, from the importer's format (ticket 08).
- [x] Test on small hand-written Recorded Games, including one with a known difference. These tests need no archive.

## Comments

### 2026-11-16 — implemented (Claude)

Every box is ticked. `uv run python -m ai.recorded_games.replay_dataset` replays every suitable Game on all cores in about 9 min. With `--sample N` it replays about N Games spread over the shards (about 45 s for 3,000) and writes nothing. It writes each shard's `replays.jsonl.gz` and `.cache/recorded-games/replays-report.txt`. The report gives the share replayed fully, overall and by setting and rating, how far the other Games get, the differences grouped by cause with example Games, and the Decisions the log left open.

**Decisions made with the user** (one opening batch, every recommendation taken):
- **The engine change.** `Settings` gains an optional `deal`: the first player, and the Corporations, Prelude Cards and Project Cards in the order they are dealt and drawn. Cards it leaves out are shuffled beneath. It is saved in the Replay, so ADR 0010 holds.
  - Games without a deal draw exactly the random numbers they did before. The old Replays in `tests/engine` still reproduce.
  - A Sampled Position drops the deal.
  - It is boxed, so copying a Game costs what it did.
- **Code and test seams.**
  - The code is `ai/recorded_games/replay.py` and `replay_dataset.py`.
  - Tests are hand-written Recorded Games in the dataset's shape: `tests/ai/recorded_games/recorded.py` and `test_replay.py`, 14 tests, no archive. The deal is tested through `tm_engine` in `tests/engine/test_deals.py` (12 tests).
  - `replay.py` joins the fair-play test's short list of files that may import the engine. It builds data and is never a Controller.
- **Format.** The dataset stores each Game's Replay rather than one record per Decision.
  - Each record holds the deal, the picks up to the first difference, the difference and the inferred picks.
  - `replay.action_decisions(record)` rebuilds each Decision outside setup and the Research phases: the Prelude Cards played and the whole Action phase. Each comes as its Player saw it, with the Player View, the Options, the pick and whether it was inferred.
  - `dataset.read_replays()` reads the records. The format note in `ai/recorded_games/__init__.py` describes them.

**How a Game is replayed** (calls made since; recommendations, no further questions):
- **The deal.** It comes from the setup records, then from every card first named in a draws, keeps, reveals or drafts line, in log order. A Research phase's deal goes in player order from that Generation's first player.
- **Setup and the Research phases.**
  - Setup, Draft and Corporation Decisions come from ticket 08's records.
  - Research buys are read from the keep lines with ticket 09's `Keep`, because 472 buy records keep a card the Player took back ("drafts X") or replaced after "cancels their move". With no keep line, the record is used; a buy of nothing has no line.
- **Actions.** Each Action's main pick comes from an "anchor" line: plays card, activates, standard project, claims, funds, passes, skips second action, a bare "pays 8 Heat" with a Temperature step, or "pays 8 Plant".
  - Some plays exist only in `card_played`, and some activations only in the move type or an "(activation effect of X)" reason. These become anchors too. A card's action counts once per Generation.
  - An activation that names no card is chosen among the card actions on offer by the trackers.
- **Picks within an Action** come from its own lines:
  - Areas: Board Game Arena's (x, y) map to Areas through a per-row offset, and named Areas map directly.
  - Payments, including Psychrophiles' microbes.
  - Look keeps, targets, alternative effects, Viral Enhancers, Olympus Conference and Resource changes.
- **Cards that leave unnamed.** Sell Patents and Mars University discards are chosen in hindsight: a card its Player never plays later, as ticket 09 decided.
  - A Mars University discard the log dropped, or an Olympus Conference pick with no line, is settled by whether the engine's draws then match the log's.
- **Picks the lines don't settle** go to whichever Option leaves the trackers and the deck as the log does once the Action is finished. M€ by the Action's own "pays/gains N M€" lines breaks ties.
  - A tie leaves the Decision open. At a later difference the replay goes back to the latest open Decision within 40 Actions and tries the next alternative, up to 30 times a Game. Otherwise the attempt that got furthest stands.
  - A look whose buy the log doesn't name stays open the same way. 5,702 retries were needed in all.
  - An unlogged placement avoids every Area the log places a Tile on later.
- **Comparisons.**
  - At each Action, the trackers that changed during the previous Action are compared with the engine's: Resources, Production, Tags, Terraform Rating, Temperature, Oxygen and Oceans.
  - Trackers lag. Media Group's +3 M€ after an Event's payment never reaches the M€ tracker, for example. So a tracker differs only when it disagrees at two of its changes in a row. The Replay is cut back to the first disagreement.
  - Resources aren't compared across a Production phase.
  - The engine must also have drawn exactly as many of the dealt cards as the log names by then.
  - A Game played to its end must finish with the log's "scores N TOTAL VP" lines. The dataset's `victory_points` come from the last game state, which can miss the final Greenery conversion (94cc11c5a843d40f: 114, while the log scores 116).
- **Log traits handled** (each found on real Games):
  - The engine plays a Player's last Prelude Card without a Decision.
  - Once the other Player has passed, End Turn isn't offered, though Board Game Arena still logs "skips second action".
  - A move typed "pass" is a pass only where the Draft's deal follows or the Generation ends; elsewhere the type can be wrong. Its Player can be wrong too: the pass goes to whoever hasn't passed (e971a019a9aebcbf).
  - Search for Life reveals "X: it does not have a Microbe tag".
  - Some versions log discard lines without their reason.
  - Lines that name a renamed account by its old name: the name is matched to the Player whose moves it starts, then dropped. That was 300,645 lines.
  - A move's lines before its anchor belong to that Action only when they are its own Player's "pays/removes" lines. Otherwise "places Greenery … | Player 2 passes" loses its placement.
- **Inferred picks are marked.** These are passes and Turn ends the log leaves out, tracker-settled ties, hindsight discards and retried alternatives. They are 3.96% of all picks, 5.8% of Action-phase Decisions in a 300-Game sample. Training can leave them out.
- **Old logs are not replayed.** These are Games without both Players' setup records. 44,714 Games have them, a few more than ticket 09's 42,431 named Games, which also required every Hand Counter check exact. The replay's own checks are stronger, so the report doesn't split them.

#### Box 1 and box 3: the run (2026-11-16, all 44,714 suitable Games, 9 min 13 s)

**Replayed fully: 32,725 of 44,714 (73.2%).** They give 16,304,718 engine Decisions before each Game's first difference, about 10 million of them outside setup and the Research phases.

| | Games | Replayed fully | Share |
|---|---|---|---|
| Prelude, not conceded | 20,217 | 14,047 | 69.5% |
| Prelude, conceded | 19,480 | 15,692 | 80.6% |
| No Prelude, not conceded | 3,271 | 1,771 | 54.1% |
| No Prelude, conceded | 1,746 | 1,215 | 69.6% |
| Lower rating below 300 | 18,173 | 13,347 | 73.4% |
| Lower rating 300–399 | 10,419 | 7,550 | 72.5% |
| Lower rating 400–499 | 8,617 | 6,304 | 73.2% |
| Lower rating 500–599 | 6,112 | 4,483 | 73.3% |
| Lower rating 600+ | 1,393 | 1,041 | 74.7% |
| 500–599, not conceded | 3,376 | 2,325 | 68.9% |
| 600+, not conceded | 872 | 607 | 69.6% |

**Games replayed partly (11,989).**
- On average they replay 59% of their moves (median 62%), with a mean of 266 Decisions before the first difference.
- Their first differences come late: 344 before Generation 1's Actions, 515 in Generation 1, and then rising to 1,516 in Generation 10. Mostly the replay reaches mid- to late Game.
- A record whose `complete` is false still holds every pick before its `difference`. `action_decisions` yields exactly those.

#### Box 2: the difference groups

The first difference of each Game, largest first:

| Group | Games | Share | Call |
|---|---|---|---|
| trackers differ: M€ | 2,325 | 5.2% | parser |
| deck out of step | 1,459 | 3.3% | parser |
| Area not offered | 1,363 | 3.0% | parser |
| card not in hand | 1,210 | 2.7% | parser |
| final scores differ | 1,150 | 2.6% | parser |
| trackers differ: Plant | 1,110 | 2.5% | parser |
| not offered: plants | 588 | 1.3% | parser |
| no card to discard in hindsight | 493 | 1.1% | parser |
| card in hand not playable | 377 | 0.8% | parser |
| log names no plays | 344 | 0.8% | parser |
| record differs: draft | 331 | 0.7% | parser |
| trackers differ: TR | 301 | 0.7% | parser |
| log has no more Actions | 211 | 0.5% | parser |
| 23 smaller groups | 1,129 | 2.5% | parser |

What lies behind each:
- **"Parser"** covers both the log leaving something out and the replay's reading of it, guessed picks included. In the groups examined, the difference follows an earlier pick the log didn't settle, or a line it never wrote:
  - an unlogged card action or placement;
  - an animal added to the wrong one of two cards (c5b160a6ea52e8ae: Livestock one short);
  - draws in an Action the log never names (7ae37f1aab60ab6c: Planner claimed with 2 cards the log doesn't name).
- **Not offered, and cards in hand not playable.** These come from M€, a Resource or the hand already short after an earlier divergence the trackers missed. Examples: Commercial District with 4 M€ (1d832a120ab01a55); Planner at 15 cards (010f545b81f2ca4b, 546d2b9d4838d390).
- **Final scores.** Checking Games with no guessed placement or card-resource pick found the dataset's stale `victory_points` (now fixed) and card Victory Points one off from a guessed add.
- **Log names no plays.** These are 344 Games whose moves say only "Player 1 other", with reasons.
- **Record differs or missing (Draft).** These come from ticket 08's records: picks missing in the last Generation, or a pick the next hand contradicts.

**Engine bugs: none found.** Every group sampled traced back to the log or to the replay's reading of it. So there is no new regression test beyond the deal's own tests.

**Board Game Arena's rulings** (rules notes in `docs/rules-notes.md`, "Recorded Games"):
- **Experimental Forest's draw order.** Board Game Arena draws the Greenery's placement bonus card after revealing; the engine draws it on placement, as the rulebook gives the bonus when the Tile is placed. The rulebook stands, and the deal puts the bonus card first, so both draw the same cards. Pinned by `test_experimental_forests_placement_bonus_is_dealt_before_the_cards_it_reveals`.
- **"Skips second action" once the other Player has passed.** This is not a disagreement: the engine already doesn't offer End Turn when it changes nothing (rules note "End Turn once everyone else has passed").
- **The deal** gets its own rules note too ("A Game from a chosen deal").

**Where to stop (decided).** The largest group is 5.2% and none of them has one cause. Each case needs digging through its log, and most trace back to a gap in the log, not to a rule. A partly replayed Game still gives its Decisions up to the difference. So the work stops here, at 73.2%. Over this session the share rose from 1% to 73% by fixing parser traits in order of size, measured on a 3,250-Game sample at each step.

#### Box 4: the dataset

- **The file.** Each shard gains `replays.jsonl.gz` (44,714 records), with the engine's Replay (deal and picks), whether the Game replayed fully, its first difference and its inferred picks.
- **The Decisions.** `action_decisions()` rebuilds the Decisions after setup and outside the Research phases. Each comes as its Player saw it, with the Player View, the engine's Options and the pick, in the shape of ticket 08's records (player, generation, kind).
- **Hidden cards.** The reader takes only `player_view` and the Decision out of the engine. A test checks that Player 1's records never name Player 2's hand.
- **Training data.** Like the slim moves, the Replays name both Players' cards, so they are raw material, never training data as they stand.

#### Box 5: tests

`tests/ai/recorded_games/test_replay.py`, 14 tests:
- the deal, setup and Prelude Cards;
- a payment and an Area;
- the known difference: a card the hand lacks, which stops there with the earlier picks kept and the unlogged pass marked as inferred;
- tracker comparison, with lag allowed once and the Replay cut back to the first disagreement;
- hindsight selling;
- the Draft deal's player order;
- buy keep lines over a wrong record;
- Board Game Arena's coordinates;
- Experimental Forest's order;
- scores taken from the log's totals;
- the reader, its fairness and an empty Replay.

`tests/engine/test_deals.py` has 12 tests of the deal.

**Code review against 48d326a** (Standards and Spec, in parallel):
- **Fixed:**
  - A tracker difference kept the picks up to its confirmation; the Replay is now cut back to the first disagreement.
  - Inferred picks weren't marked; they now are, in the records and in `action_decisions`.
  - "pays 8 Heat" by Helion paying for a card could count as a heat conversion.
  - The engine's three `match deal { … }` blocks are now one `Game::dealing_order`. Shuffling with nothing stacked draws the same random numbers, and the old-Replay tests confirm it.
  - `read_replays` reuses `read_lines`.
  - Names: `step` became `answer_next_decision`, and `ChoicePoint` became `OpenDecision` (the glossary avoids "step" and "choice").
  - An unused `ties` field; a pointless rebinding in `Game::new`; lines over 120 columns in the new tests (a `play` helper); a hard-coded Game count.
- **Left as is:**
  - "Cards that entered unnamed take their names from their plays." Named Games almost never have unnamed cards. A card named only at its play has no known place in the deck, so its Game stops at "card not in hand" or "deck out of step".
  - Named Games aren't split from the other Games with records in the report (see above).
  - A tracker disagreeing only at its very last change isn't reported. It may be lag, and the final scores are checked.
  - Experimental Forest's reorder needs a keeps line: old logs give "reveals X: it has a Plant tag", but old logs aren't replayed.
  - A Research deal's first player is counted from the earlier deals rather than read from the Generation. One missed deal would shift the rest; the Draft records then show it as "record differs: draft" (0.7%).
  - A `ValueError` from the engine doesn't backtrack. It never occurred in the full run.
  - `RecordedGameReplay` does four jobs: reading the log, the deal, backtracking and comparing. Its cursor fields travel as a dict. `Anchor.kind` is a string. `RESOURCE_KEYS` overlaps `TRACKERS`. All are worth tidying if ticket 14 extends the replay.

**Checks:**
- 2,137 tests pass under `timeout`.
- `cargo clippy` and `cargo fmt --check` are clean in `engine/`.
- `uvx --offline ruff check` and `ruff format --line-length 120` are clean on the touched files, with the parentheses in `except (A, B):` restored by hand.
- No GUI change.
- The README's "Recorded Games" section gives the replay and its numbers.

**Open points:**
- The groups above, if ticket 14 wants more Games. The largest, the M€ tracker, mostly hides an earlier guessed pick.
- `tie: viral_enhancers` (31,373) is mostly a plant against a Card Resource that the lagging trackers can't tell apart. These picks are marked inferred.
- The slim moves of renamed accounts still hold their old names (ticket 09's open point). The replay drops them.
