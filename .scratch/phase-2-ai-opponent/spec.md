Status: ready-for-agent

# Spec: Phase 2 — an AI opponent that beats me

## Problem Statement

Phase 1 gave me a correct, fast Terraforming Mars, but the only opponent is a Random Bot. I want an AI that beats me in most 2-player Games without seeing cards it shouldn't.

Self-play from nothing is slow on my laptop, and a quick test shows how far simple bots are from human play. There are also about 59,000 suitable Games played by humans on Board Game Arena, most of them with Prelude, which the engine doesn't have yet.

## Solution

Phase 2 has two parts:

1. **Add Prelude to the engine**, as a setting of each Game (ADR 0011).
2. **Build a ladder of Controllers** (ADR 0013), each playable and each the benchmark for the next:
   - the **Card Economy Bot** compares Options by their Prices;
   - the **Imitation Model** learns from strong Players in Recorded Games (ADR 0012);
   - the **Value Model** improves past them by self-play;
   - **search with Sampled Positions** adds strength at play time.

Phase 2 is done when all of these hold:
- Prelude is implemented and tested to phase 1's standard;
- no Controller can see hidden cards, and tests show it;
- the final Controller wins a Match against each earlier one;
- I lose most of a set of recorded Games to it in the GUI (ticket 17 fixes the number before play starts).

## What we measured

Measured on 2026-11-06. The scripts are in `experiments/` next to this spec. Bots in the tables played without Prelude.

**Engine, 2 Players:** 55,000 Random Bot Games per second on 16 cores, a copy in under 1 µs, a random playout from mid-Game in about 100 µs, a Player View in 41 µs (18 KB).

**Quick bots.** The heuristic was the cost-return idea, written in minutes. The search bot ran N random playouts per Option and could see the hidden cards, so its numbers flatter it.

| Match | First bot's win rate | Victory Points | Generations |
|---|---|---|---|
| Heuristic vs Random Bot | 100% (400 Games) | 117–53 | 18.5 |
| Search with 5 playouts vs heuristic | 3% ±3 (112) | 66–99 | 16.2 |
| Search with 20 playouts vs heuristic | 30% ±9 (112) | 80–90 | 15.8 |
| Search with 100 playouts vs heuristic | 84% ±10 (56) | 96–81 | 15.1 |

The first heuristic stalled: two copies never finished a Game, because each terraforming step shortened its estimate of the Generations left and so lowered the worth of everything it owned. Holding that estimate fixed at the Decision fixed most of it, though 4 of 200 Games still stalled. Search at 100 playouts cost about 26 CPU-seconds per Game.

**Recorded Games:** 2 Players, Tharsis, Corporate Era, Draft on, Colonies off. Counts are distinct Games in the archive. Ratings are Board Game Arena's `game_rank`, using the lower of the two Players' ratings.

| | With Prelude | Without Prelude |
|---|---|---|
| All Games | 51,422 | 7,622 |
| Not conceded | 32,125 | 5,865 |
| Not conceded, both rated 500+ (450+ without Prelude) | about 6,000 | about 780 |
| Not conceded, both rated 600+ | about 1,400 | 42 |
| Mean Generations | 10.7 | 12.4 |
| Mean Victory Points, winner–loser | 106–87 | 105–82 |
| Mean card Victory Points of the better Player | 28 | 28 |

Stronger Players play closer Games: the winning margin falls from about 30 Victory Points in the lowest rating band to about 11 at 600+.

## User Stories

### Prelude

1. As a player, I want to switch Prelude on or off when I start a Game, so that I can play either way.
2. As a player, I want Prelude Cards dealt, chosen and played as the rules say, so that setup is correct.
3. As a player, I want all 35 Prelude Cards, 5 Corporations and 7 Project Cards to work as printed and be drawn like other cards, so that I play the full expansion.
4. As a developer, I want Games and Replays without Prelude to stay exactly as they are, so that the rules tests and old Replays stay valid.

### Comparing Controllers

5. As an AI developer, I want one command that plays a Match between two Controllers and reports the win rate with its uncertainty, Victory Points, Generations and card Victory Points, so that every claim of improvement is measured.
6. As an AI developer, I want a Controller to receive only the Player View, the Decision and a way to get Sampled Positions, so that it can't reach hidden cards.
7. As a player, I want to choose any finished Controller for a Player on the setup screen, so that I can play against it.
8. As a player against an AI, I want its Decisions to take at most a few seconds, so that the Game is pleasant to play.

### Looking ahead fairly

9. As an AI developer, I want a Sampled Position for any Player at any Decision, so that lookahead never uses cards that Player can't see.
10. As an AI developer, I want two Games with the same Player View and seed to give the same Sampled Position, so that a test can prove hidden cards have no influence.

### Recorded Games

11. As an AI developer, I want Recorded Games turned into a compact private dataset of one Player's view of each Decision and what they picked, so that training doesn't re-read 147 GB of JSON.
12. As an AI developer, I want to filter that dataset by rating, Prelude, conceded Games and date, so that I can choose whom to learn from.
13. As an AI developer, I want the opponent's hand and the deck removed from every training position, with a test to check it, so that no model learns from what it couldn't see.
14. As an AI developer, I want each Player's hand rebuilt at every Decision in a Recorded Game, so that Action-phase Decisions can be learned from.
15. As a rules tester, I want Recorded Games replayed through the engine and every difference listed, so that real play tests the rules beyond what fuzzing can.

### The ladder

16. As an AI developer, I want a Card Economy Bot built on Prices, starting from those fitted to Recorded Games, so that there is a strong, explainable benchmark.
17. As an AI developer, I want Decisions and Options encoded as numbers, with computed strategy facts as inputs, so that models can learn from them.
18. As an AI developer, I want an Imitation Model for Draft and buy Decisions, and then for all Decisions, so that training starts from competent play.
19. As an AI developer, I want a self-play loop that starts from the Imitation Model and trains a Value Model within my laptop's limits, so that the AI can improve past the Players it copied.
20. As an AI developer, I want search at play time using Sampled Positions and the Value Model, so that spare seconds per Decision become strength.
21. As a player, I want to play a recorded set of Games against the final Controller, so that the goal is decided by real results.

## Implementation Decisions

### Shape of the system

- The system keeps its layers: Rust engine → Python engine module → local Python server → GUI. Controllers, training and tools are Python, and anything that proves too slow moves into the engine.
- New Python code goes in a new top-level `ai/` package, which depends on the engine module and never the reverse. The server imports Controllers from it.
- PyTorch is added as a dependency once ticket 13 needs it. A dry run on 2026-11-06 resolved torch 2.15.0 and numpy 2.5.4 for Python 3.14; GPU use on the RTX 3050 is unverified.

### Fair play

- The Controller seam is one method: given a read-only handle, return the index of an Option. The handle offers the Player View, the Decision and Sampled Positions, and never the Game.
- A Sampled Position is made inside the engine from what the Player View says. The cards the Player can't see are those not visible to them; those they passed in the Draft are known to be with the Player they passed them to, unless since played or otherwise accounted for.
- This replaces trying Options on copies of the real Game, which leaks the deck through draws (ADR 0013). The quick bots above leaked this way.

### Prices

- Starting Prices come from the published fit in `analysis/model_predict.py` and `CORP_VALUES_REPORT.md` of bga-tm-scraper. They are numbers to check, not code to copy: the repo names no licence.
  - MC Production 5.7, steel Production 10, titanium Production 14, plant Production 9, energy Production 7, heat Production 4.5.
  - Science Tag 3.6 (about 6 over a whole Game); Earth, space, plant and Jovian Tags 1.
  - A card at setup 4, a City Tile 9, an average Corporation 68.
- These are for cards bought in Generation 1 of Prelude Games, and rate a Victory Point at only 1.5 MC. So Prices must depend on the Generations left, and a Victory Point's Price must rise over the Game towards the cost of buying one with Standard Projects.
- A Tag's Price depends on context, such as how much closer it brings the Requirements of cards in hand, and what it triggers on played cards.
- The estimate of the Generations left is held fixed while comparing a Decision's Options, or the bot refuses to terraform.
- For setup and Awards, tfmstats.com's tables give further starting values (see "Statistics from tfmstats.com").

### Models

- Models score each Option given the position, so the same model handles any Decision and any number of Options (ADR 0002).
- Cards are inputs in their own right: a learned identity plus printed facts (cost, Tags, Requirements, Victory Points, effect data), so that a model can learn synergies between cards in hand and in play.
- Strategy facts are inputs too: Generations left, each card's payback, distance to its Requirements, and Prices. Models may overrule them (ADR 0013).
- Models must fit a 6 GB GPU and train within 12 GB of RAM. Size is chosen by those limits and tested by Matches, not fixed here.
- Training optimizes winning. Victory Point margin may be used as a secondary signal to reduce noise, because the goal is to beat me, not to score high.

### Recorded Games

- The archive is `tm_statistics/`: gitignored, 147 GB, one JSON file per Game and perspective. No file in it is ever run. The derived dataset goes in `.cache/`, with player names dropped.
- Disk space is limited: 58 GB was free on 2026-11-06. The derived dataset should be well under 10 GB; once it exists, I decide whether to delete the archive.
- Known traits of the logs:
  - 1,842 `.azDownload-*` files are empty and are skipped.
  - About 24% of Prelude logs and 35% of the others lack the dealt cards, and are left out of imitation where they are needed.
  - `player_hands` is always empty.
  - The `Hand Counter` tracker is often stale.
  - "cancels their move" lines occur, and some moves are credited to the wrong Player.
  - Wording differs by scraper version.
  - Names differ from the card catalog (Allied Bank/Allied Banks, CEO's Favourite/Favorite Project).
- Conceded Games are usable for Decisions, but not as evidence of final scores.
- Some of the archive's dates are invalid, so a date filter must treat those as unknown.

### Statistics from tfmstats.com

tfmstats.com shows tables built by the same open-source scraping project as the archive, whose data it says is "freely available to the community" (checked 2026-11-13). Each is per item, with win rate, average rating change and counts:
- Starting Hand: each card's keep rate when offered at setup, and the rating change when kept or not. 2 Players, ranked, Prelude and Draft on, no Colonies.
- Project Cards: when played, or when offered.
- Corporations and Preludes: when chosen or kept.
- Combinations: pairs of Corporation, Prelude Card and starting-hand card, with each pair's lift over its parts. Same games as Starting Hand.
- Milestones and Awards: when claimed or funded, with the mean Generation, and for Awards how often the funder doesn't win it (flip rate).

How they are used:
- **As checks:** the importer's tables should match them (ticket 08), and Controllers' setup choices, keep rates, synergies and Milestone and Award timing are compared with them (tickets 11, 13 and 14).
- **As starting values:** for setup Prices and for funding Awards (ticket 11).
- **Never as training data or fixed rules** (ADR 0013): a win rate when a card is played or a Milestone claimed mostly shows who was already ahead.
- **Never as model inputs as they stand:** they include the held-out Games. Per-card statistics as inputs are computed from the training Games (ticket 12).

Things to know: only Starting Hand and Combinations are fixed to our kind of Game; the other pages start with no filters (every player count, map and expansion) and remember the filters set, so press Reset afterwards. They include other expansions' Corporations and other maps' Milestones and Awards, and names the scraper failed to translate ("Begginer Corp", "Milestone 5", "card_prelude_P34", Award names in Polish). The pages need JavaScript, so read them in the browser pane.

### What ticket 09 starts from

A first rebuild, from the wording of move descriptions, finds 99.5% of played cards in the hand without Prelude and 98.6% with. But it is about 2 cards too large, and matches the `Hand Counter` at only about 48% of checks after a card is played. Additions look reliable, and some removal is being missed. Sell Patents is a suspect, not a finding. The script is `experiments/logs_hands2.py`.

Result (ticket 09):
- The missed removals are discards that never name their cards (Sell Patents, Mars University), plus a dozen wording traits.
- `ai/recorded_games/hands.py` now rebuilds hand size to 99.2% of fresh Hand Counter checks, and 97.2% of Games at every check.
- Ticket 09's Comments say which Games to trust and the accuracy tickets 10 and 14 need.

### Build order

1. **Prelude:** tickets 01–05.
2. **Foundations:** tickets 06–07, the Match tool and fair Controllers, then Sampled Positions.
3. **Recorded Games:** tickets 08–10.
4. **The ladder:** tickets 11–16.
5. **The verdict:** ticket 17.

Tickets 06 and 08 can start alongside Prelude work, since neither needs it finished.

## Testing Decisions

- **Rules:** as in phase 1. Tests go through the Python engine module, read like play, and every new card has a scenario test. Prelude joins the fuzzer and the coverage and mismatch checks.
- **Fairness is tested directly:**
  - two Games with equal Player Views and different hidden cards give equal Sampled Positions for the same seed, and equal picks from any Controller given the same random state;
  - no Recorded Game position in the dataset holds the opponent's hand or the deck.
- **Data:** the importer is tested on small hand-written log snippets, including each known oddity. Tests never need the archive, because it isn't in git. Coverage figures come from a separate command run on the real archive.
- **Strength:** measured by Matches, not unit tests. A Match reports its uncertainty, and a Controller moves up the ladder only if the interval on its win rate against the one below sits above 50%.
- **Models:** tests cover shapes, encoding and fairness, plus a small training run that overfits a few positions. They don't assert strength, and they need no GPU.
- **Prior art:** `tests/fuzzing/` for many-Game runners, `tools/benchmark.py` for commands that report and exit with a status.

## Out of Scope

- Other Player counts for the AI. It trains and plays 2-player Games only. Games with 3–5 Players keep working, with humans and Random Bots.
- Difficulty levels as a feature. Earlier rungs remain selectable, which covers most of it for free.
- Other maps, Colonies, Venus Next, Turmoil and promo cards, even though the logs hold some of them.
- Running the scraper to fetch more Games. It needs a Board Game Arena login and has daily limits, and the archive is enough to start.
- Copying code from bga-tm-scraper or the open-source game.
- Publishing the logs, anything derived from them, or a trained model.
- An AlphaZero-style training loop (ADR 0013). It can be reopened if search and the Value Model stall below the goal.

## Further Notes

- **Steps that need my OK when reached:** installing PyTorch; deleting the archive; long training runs that keep the laptop busy for hours.
- **Rules authority** is unchanged (ADR 0001). Board Game Arena's behaviour is a further reference for Prelude, but when a Recorded Game differs from the engine, the rulebook decides. A difference may be Board Game Arena's own ruling and not our bug.
- **Rule bugs** found by Recorded Games or by play get a ticket with a Replay and a regression test, as in phase 1.
- **Sources:**
  - [tfmstats.com](https://www.tfmstats.com/), for the statistics and the archive (dated 2026-01-10);
  - [bga-tm-scraper](https://github.com/HStrand/bga-tm-scraper/), for the log format and the Prices;
  - [TAG: Terraforming Mars](https://rdgain.github.io/assets/pdf/papers/gaina2021terraforming.pdf), for earlier MCTS results.
- **Glossary and decisions:** CONTEXT.md, and ADRs 0011–0013.
