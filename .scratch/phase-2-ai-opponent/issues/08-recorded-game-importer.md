# 08 — Recorded Game importer

**What to build:** A command that reads `tm_statistics/` and writes a compact private dataset to `.cache/` (ADR 0012): the Games' settings and results, and for now each Draft and buy Decision, with what that Player could see and what they picked.

Each record describes one Player's Decision: the cards on offer, those kept so far, and the public state from the per-move trackers (Global Parameters, Resources, Production, Tag counts, Terraform Rating, cards played, Milestones, Awards), and both Players' ratings and the result. Action-phase Decisions come after tickets 09 and 10, so the format must leave room for them.

Start from `experiments/logs_scan.py`, which scans the archive on all cores. No file in the archive is ever run, and it is read with `python -I` or equivalent.

**Known traits to handle:** see "Recorded Games" in the spec. In particular, card names need a map to the catalog, wording differs by scraper version, and several perspectives of one Game count once. tfmstats.com's tables, built by the same scraper, show names it failed to translate: "Begginer Corp", "Milestone 5", "card_prelude_P34" and Award names in Polish ("Podróżnik", "Bankier"). Expect the same in the archive.

**A cross-check:** tfmstats.com publishes tables computed from the same kind of logs (see "Statistics from tfmstats.com" in the spec). Computed from the dataset with the same filters, ours should come close to the site's. That checks name mapping, offers, keeps and duplicate perspectives better than total counts do. Set the site's filters to 2 Players, Tharsis, Prelude, Draft and no Colonies where a page has them, record the date, and press Reset afterwards (the site remembers its filters).

**Blocked by:** 01 — Prelude cards in the catalog

**Status:** ready-for-agent

- [x] One command builds the dataset, using all cores, resumes after interruption, and reports coverage: Games read, skipped and why, by setting, rating and scraper version.
- [x] Filters: 2 Players, Tharsis, Corporate Era, no Colonies, Draft on. Prelude, conceded, rating and date are stored so that training can choose.
- [x] Every card name in the kept Games resolves to a catalog id, or the report lists it.
- [x] Test on hand-written snippets: each known trait, including "cancels their move" and a duplicate perspective.
- [x] Test: no record holds the opponent's hand, the opponent's Draft cards, or the deck. Cards a Player passed on stay visible to that Player, as in the Player View.
- [x] Player names aren't in the dataset; anonymous ids and ratings are.
- [x] The dataset is well under 10 GB, and its size is recorded under Comments. Then I decide whether to delete the archive.
- [x] `tm_statistics/` and the dataset stay out of git.
- [x] Counts are compared with the spec's table, and any difference is explained under Comments.
- [x] The dataset's tables are compared with tfmstats.com's, dated, and differences beyond what the archive's date and the site's filters explain are investigated: starting-hand keep rates of the 20 most- and 20 least-kept cards; each Corporation's and Prelude Card's times chosen or kept and its win rate; and the times each Tharsis Milestone is claimed and Award funded, with the mean Generation.

## Comments

### 2026-11-13 — implemented (Claude)

Every box is ticked. `uv run python -m ai.recorded_games` builds the dataset in `.cache/recorded-games/`. Its
format is in `ai/recorded_games/__init__.py`. `uv run python -m ai.recorded_games.tables` prints the comparison
tables, and `ai.recorded_games.dataset.read_games()` and `read_moves()` read the dataset back.

**Decisions made with the user** (one opening batch, every recommendation taken):
- **Seams:**
  - Pure functions on log dicts: `import_game(log, salt)` returns an entry or raises `Skipped`;
    `choose_perspective(logs)` and `slim_moves(log, salt)` are separate.
  - The command is tested on tiny archives of hand-written logs in a temp folder.
- **Format:**
  - Gzip JSON Lines in 128 shards, one line per Game.
  - Each Game holds its settings, its results and its Decision records.
  - The public position is stored once per Research phase, and Decisions point to it.
- **Duplicate perspectives and the opponent's cards:**
  - Per Game, the most complete log is kept: dealt cards named, then offers, then keeps, then scraper version.
  - Each Player's records hold only what that Player saw.
- **Slim moves:**
  - Each kept Game's moves are also kept, so deleting the archive doesn't block tickets 09–10.
  - Names become "Player 1"/"Player 2" and ids become places.
  - Timestamps are dropped, and each game state is stored as what changed since the last.
  - Like the logs, these moves name both Players' cards. They are raw material for 09–10, never training data.

**Calls made since** (recommendations, no further questions):
- **Names:** the catalog is read from `engine/cards/cards.json`, which the engine embeds. The fair-play test keeps
  `tm_engine` out of `ai/` except the Controller seam and the Match tool.
- **Anonymous ids:** salted SHA-256 of the table and player ids. The salt is random, in `.cache/recorded-games/salt`;
  keep it to follow a Player across rebuilds.
- **Filters:** 2 Players, Tharsis, Corporate Era, the Draft, and no Colonies, as asked. The Beginner Corporation is
  also skipped, because the engine doesn't have it. Prelude, conceded, rating (`game_rank` and its change) and date
  are stored.
- **The public position at a Research phase:**
  - The trackers lag the play: a Player's counters often refresh only when they act.
  - So Resources are worked out from the previous Generation's last trackers by the Production phase.
  - Checked by hand on 2 Players, against their next refreshed M€: the computed figure minus the buy and their first
    payment matches.
  - The setup position is the rules' starting position, not the log's first game state. Otherwise a log that
    starts after a keep would show the opponent's secret setup.
- **Missing, by design:** the hand and the board's Tiles. Ticket 12 must mark them missing; they come from 09 and 10.
- **Rating:** "rating" alone means Board Game Arena's rating. CONTEXT.md gains this as a flagged ambiguity.

**Traits found in the archive, each with a test on a hand-written log** (`tests/ai/recorded_games/test_traits.py`):
- **The Draft:**
  - The last card of each round often has no pick move and sometimes no one-card hand. It is taken as the card the
    other Player passed last.
  - Pick lines are sometimes missing, credited to the other Player, or name the wrong card. A pick is read from the
    next hands instead: in a 2-player Draft, what you pass is exactly the other Player's next hand. The pick line is
    used only when no next hands follow.
- **Buys:**
  - Some versions log one card at a time ("keeps Research | pays 3 MC") and repeat or summarise later. A keep of
    several cards is the whole buy, and a keep of one adds to it.
  - After a Player "cancels their move", their next keep starts the buy again.
  - Buying nothing leaves no line. It is inferred only when the other Player's keep is logged, and not in the last
    Generation of a conceded Game.
- **Players and results:**
  - A played card is credited to whoever the description names.
  - The winner is the Player Board Game Arena places first (`elo_data.position`). The log's `winner` is "Unknown" or a
    since-changed name in 1,181 Prelude Games (2.3%), which first left every win rate 1.2 points low.
  - The result's Corporation is sometimes "Unknown"; it is then taken from the setup keep.
- **Names and dates:**
  - Untranslated and variant names: "Eccentric Sponsor", "Allied Bank", "CEO's Favourite Project", "card_prelude_P<n>"
    (by number), and the Polish Award names seen on tfmstats.com (Potentat Ziemski, Bankier, Naukowiec, Magnat
    Cieplny, Górnik).
  - Invalid dates ("0001-01-01", "1-01-01") become unknown.
- **Old logs:**
  - Versions "2025july30", no version, and some early v2025.07 logs have no dealt cards, offers or keeps.
  - Their Games keep settings and results only; 14,201 of the kept Games have no Decisions.
  - Their "You draft X" lines could give the perspective Player's buys later.
- **The fairness test** (`test_no_record_holds_cards_hidden_from_its_player`):
  - Ada's records and the positions they point to hold none of Bo's unplayed dealt cards, nor the card Bo took from
    his first Draft hand. The same holds for Bo.
  - Played cards and passed cards do appear.

**The real run** (2026-11-13, on mains):
- 105,221 files and 97,335 Games (6,044 further perspective files) in 8 min 17 s on all cores. 128 shards; an
  interrupted run resumed with only the missing shards (tested).
- Kept: 59,039 Games, 44,838 with Decisions. Failed: 0. Names not mapped in kept Games: none.
  - Skipped: 3 Players 17,633, Hellas 14,174, no Draft 3,119, Elysium 1,056, 4 Players 583, Vastitas Borealis 545,
    Amazonis Planitia 342, Colonies 324, map "Random" 266, no Corporate Era 186, 5 Players 60, Beginner Corporation
    5, and 3 maps named in Japanese or Russian.
  - Kept by the lower Player's rating: below 300 24,191, 300–399 13,891, 400–499 11,353, 500–599 7,646, 600+ 1,932,
    unknown 26. By scraper version, from v2025.10.07.1844 (20,736) down; `report.txt` has the table.
- **Decisions:** setup 89,428, Draft 2,580,232 and buy 854,742.
  - Of each Player's Research phases in Games with Draft Decisions, 99.2% are complete (3 picks and a buy).
  - 4,830 have the picks but no buy, mostly the last Generation of conceded Games.
  - 2,234 are missing picks, likewise.
  - 4 have 5 picks, probably a Generation number that goes back; left as is.
- **Size:** 1.02 GB. Decision records 0.23 GB, slim moves 0.79 GB. The tables command peaks at 0.58 GB of memory;
  its first version held whole Games and was killed for lack of memory.
- **Git:** `tm_statistics/` and `.cache/` are ignored by `.gitignore` (checked with `git check-ignore`).

**Against the spec's table** (Prelude / without):

| | Spec | Dataset |
|---|---|---|
| All Games | 51,422 / 7,622 | 51,422 / 7,617 |
| Not conceded | 32,125 / 5,865 | 31,942 / 5,847 |
| Both rated 500+ (450+ without) | about 6,000 / about 780 | 5,923 / 770 |
| Both rated 600+ | about 1,400 / 42 | 1,371 / 40 |
| Mean Generations | 10.7 / 12.4 | 10.7 / 12.4 |
| Mean Victory Points, winner–loser | 106–87 / 105–82 | 106–87 / 105–82 |
| Card Victory Points of the better Player | 28 / 28 | 28.5 / 28.0 |

- **Without Prelude, 5 fewer Games:** the 5 Beginner Corporation Games.
- **Not conceded, 183 and 18 fewer:**
  - The perspective files of 499 Prelude Games and 56 others disagree on `conceded`.
  - The spec's scan read whichever file came first; the importer reads the most complete.
- **"Better Player":** the spec meant the higher card Victory Points of the two. The winner's mean is 23.6 / 23.7,
  and the tables print both.

**Against tfmstats.com** (read 2026-11-13 in the browser pane; filters 2P, Tharsis, Prelude on, Colonies off,
Draft on; every page reset afterwards):
- **Size:** the site has about 2.7 times as many Games. It has 210,832 Corporations chosen, against our 79,394 from
  39,697 Prelude Games with dealt cards. Our archive ends 2026-01-10, so most of the site's Games are newer.
- **Starting-hand keep rates** (the site's 215 cards, all in the dataset):
  - Pearson r 0.9955, and a mean difference of 2.0 percentage points.
  - The 20 most-kept cards match within −1.0 to +0.6 points; the 20 least kept within −2.1 to +2.7.
  - Larger differences, site against ours, all near 3,700 offers each: Tardigrades 29.2% / 14.9%, Subterranean
    Reservoir 68.3 / 78.5, Black Polar Dust 28.7 / 38.7, Lava Tube Settlement 59.2 / 49.7, Carbonate Processing
    45.6 / 53.6, GHG Factories 58.2 / 66.1, Commercial District 65.1 / 57.4 and Corporate Stronghold 50.0 / 42.3.
  - These are investigated but not explained. In our data each is steady by quarter from early 2025 to January 2026
    (Tardigrades 14–16% in every quarter), so the archive's dates don't explain them. They may come from play or
    Board Game Arena changes in 2026, which the site has and we don't, or from how the site counts.
- **Corporations:** share of choices r 0.990, win rate when chosen r 0.997, with a mean win-rate difference of 0.5
  points. Point Luna, Vitor and Valley Trust are chosen 0.4–0.5 points more often in ours.
- **Prelude Cards:** share r 0.983, win rate r 0.994, mean win-rate difference 0.7 points.
  - Two cards are chosen more often in ours: Allied Banks (4.82% of keeps against 3.71%) and Excentric Sponsor
    (1.48% against 1.11%).
  - These are exactly the two whose logged names differ from the catalog ("Allied Bank" 12,133 times and "Excentric
    Sponsor" 3,519 times in setup keeps). The importer merges them, so the site probably loses some under another
    spelling.
- **Milestones and Awards:**
  - Each one's share of claims or fundings is within 0.5 points of the site's.
  - Mean Generation is within 0.16; win rate of who did is within 1.3 points.
  - The site lists the Polish Award names as separate rows, with Generation 0.0 and a 100% flip rate. We map them.

**Code review against af89b5a** (Standards and Spec, in parallel):
- **Fixed:**
  - Names were replaced in card fields of the slim moves. A Player named "Moss" would have renamed the card; now only
    descriptions and reasons change.
  - A log with no winner and no names marked both Players winners.
  - The setup position could show the opponent's secret keep.
  - Without one-card hands, the last card was lost and the buy dropped.
  - The fairness test's hidden set now includes Orbital Construction Yard.
  - `"preludes"` became `"prelude_cards"`, and `"states"` became `"positions"`, matching the tests' language.
  - One `game_id()` and `scraper_version()`; `claims_table`; `mean()` reused; an unused parameter and field removed.
  - Tests share `SALT` and `decisions()` from `logs.py`.
  - The docstrings now say how download leftovers are grouped and that a finished shard isn't reread after the
    archive changes.
- **Left as is:**
  - `Reader` keeps parallel per-Player dicts. A per-Player Research record would be tidier; worth doing if ticket 09
    adds hand tracking here.
  - Player ids and places both travel through `Reader`.
  - The `(kind, key)` pairs for Milestones and Awards.
  - Win rates for claimers and the Research-phase completeness count weren't asked for. Both are cheap, and the
    completeness count found the buy traits above.
- **Open points:**
  - Only card names the importer uses are checked against the catalog. Names in other moves (draws, Action-phase
    looks) go into the slim moves unchecked; ticket 10 will meet them.
  - tfmstats.com's Starting Hand page is "ranked" Games only; the logs carry no ranked flag, so ours can't filter it.
  - A conceded flag taken from any perspective, not just the kept one, would be safer for final scores.
  - A Player who cancels and then buys nothing keeps the cancelled buy.
  - The 8 keep rates above.

**Checks:**
- 2,085 tests pass in 60 s, 67 of them new, under `timeout`.
- `uvx --offline ruff check` and `ruff format --line-length 120` are clean on the new files.
- No engine or GUI change, so no clippy, rustfmt or GUI build.
- The README gains a "Recorded Games" section.

**The archive** (2026-11-13): the user keeps `tm_statistics/` for now. Whether to delete it is asked again later.
