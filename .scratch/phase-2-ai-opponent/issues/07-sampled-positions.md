# 07 — Sampled Positions

**What to build:** An engine operation that makes a Sampled Position for a Player at any Decision, exposed through the Python engine module and through the Controller handle.

It deals the cards that Player can't see at random: the deck and other Players' hidden cards, including cards under way in Draft, buying or Prelude setup. It uses only what the Player's own Player View holds, including what they passed in the Draft. Hand sizes and deck size stay right, and all Decisions still in progress stay answerable.

Decide with care what happens to a Decision belonging to another Player while the sample is made, since its Options depend on cards that are now different. A sample may need to start from the last point where the Decision is the Player's own.

This must be fast, because search calls it thousands of times per Decision. Aim to stay in the microseconds, like a copy (ADR 0004).

**Blocked by:** 02 — The Prelude setting and setup; 06 — Matches and fair Controllers

**Status:** ready-for-agent

- [x] Test: two Games that differ only in hidden cards, with equal Player Views, give equal Sampled Positions for the same seed. This is the proof of fairness, and it covers every Decision kind reachable in a fuzz run.
- [x] Test: a Sampled Position's Player View for that Player equals the real one.
- [x] Test: card count is conserved, no card appears twice, and cards the Player passed in the Draft stay with the Player they went to unless played or otherwise accounted for.
- [x] Fuzzed: a Sampled Position taken at any Decision can be played to the end with `play_randomly`, without error, over a large run.
- [x] Cards known to be with a specific Player, such as ones they drew through a public effect, are handled, or the limits are listed in the rules notes with why they are acceptable.
- [x] The benchmark reports the time per Sampled Position.
- [x] A flat playout Controller using Sampled Positions runs a Match against the cheating version in `experiments/bots_experiment.py`, and the cost of playing fair is recorded under Comments.

## Comments

## Comments

### 2026-11-12 — implemented (Claude)

Every box is ticked. The engine's new `sampling.rs` makes Sampled Positions. `tm_engine.Game.sampler(player)` returns
an opaque `tm_engine.Sampler`, whose only method, `sample(seed=...)`, returns a new Game. A Controller gets them
through `handle.sample(seed=...)`. The Flat Playout Bot (`ai/flat_playout.py`, registered as `flat_playout`) is the
first Controller to use them.

**Decisions made with the user** (one opening batch, every recommendation taken):
- **The seams:**
  - The Sampler holds the position inside Rust; the handle holds a Sampler and makes samples only when asked.
  - So the leak test stays strict: no Game is reachable from a handle.
  - A sample has its own seed, an empty log, a Replay that starts `"sampled"` (it can't be rebuilt) and only its
    Player's own Draft passes. Its Decisions count from 0.
  - The handle's Decision lost its `sequence` number, which leaked how many cards another Player had bought before
    you (one pick each). The server and Match tool keep their own.
- **Other Players' choices in the current simultaneous step** (the card kept in this Draft round, or the Corporation
  chosen, Prelude Cards kept and cards bought) are taken back in a sample and asked again after the Player's own.
  - The engine gained `Buying.done` and `Drafting.picked`, and `next_in_player_order_who` looks past the last Player
    and back to the first.
  - In a real Game nobody before the current Player is still to pick, so real Games are unchanged. The suite's
    Replays and the benchmark's mean Generations (20.99 and 17.87, as before) agree.
- **The Match:** the same Flat Playout Bot on both sides, 20 playouts per Option. The cheating side's handle gets a
  sampler that returns copies of the real Game (`experiments/cost_of_fair_play.py`).

**How a sample is made** (details and reasons in `docs/rules-notes.md`, "Sampled Positions"):
- The Sampler keeps the position with every hidden place emptied, so it holds no hidden card itself.
- It keeps the cards the Player can't see in a pool per kind: Project Cards, Corporations and Prelude Cards. Pools are
  the whole set for the Game's settings minus what the Player sees, not the cards in hidden places, since the cards
  that left the Game unseen differ between Games the Player can't tell apart.
- Each sample deals the pools afresh into the same places with the same counts: other hands, Draft and buying cards,
  cards another Player is looking at, Corporations and Prelude Cards dealt, Prelude Cards kept, the deck order, the
  discard pile and the Prelude deck.
- **Cards the Player passed in the Draft** stay with whom they went to last. The last pass in this Draft is exactly
  what that Player picks from now; the rest go to their Draft keeps, their cards to buy, or their hand.
- **Found while building:**
  - **The fuzzer:** a card another Player is paying for is still in their hand, so it was dealt elsewhere, then
    played: in two places. It stays in their hand now, and every Player View names it (`playing_card`), as a played
    card is face up.
  - **The fuzzer:** another Player in the middle of Excentric Sponsor could be dealt a hand with nothing it can play.
    The sample is then dealt again from the same random numbers, at most 1,000 times. Everyone knows they hold such a
    card, so this stays fair.
  - **The code review:** another Player's keeps so far among cards they look at were kept, which leaked the order of
    their secret picks. They are taken back now, until they pay, when everyone sees how many.
  - **The new real-positions test:** what the current Player is doing (selling patents, say) was in the Game but not
    in the Player View, so two positions a Player couldn't tell apart gave different samples. Every Player View now
    has `deciding`, the kind of the current Player's Decision, as everyone at the table sees it. While Players buy, it
    is "buy_cards" throughout, as how far each has got is secret. `Game::decision_kind` gives the kind without
    building Options.
- **Limits (box 5)** are in the rules notes, "What a Sampled Position doesn't know":
  - cards revealed publicly (Search for Life, reveal-until-found Prelude Cards);
  - unplayable Prelude Cards discarded, and Valley Trust's discards;
  - the Player's own discards (the largest gap);
  - Prelude Cards not kept at setup;
  - with 3+ Players, where passed cards went next;
  - passed cards left unbought.

  None makes a sample better informed than the Player View. A later fix would be a Player View list of the cards its
  Player knows are in the discard pile.

**Fairness tests** (`tests/engine/test_sampled_positions.py`, 12 tests):
- **Two Games that differ only in hidden cards** (a Scenario with the hand, deck, discard, Prelude Cards and seed
  swapped) give the same sample: full view, Decision, log, seed and Replay, now and after playing both out.
- **Real positions a Player can't tell apart:** in 6 whole Games (2 to 4 Players, Draft and Prelude on and off), at
  every pick where some other Player's view didn't change, both positions give that Player the same sample. 928
  pairs are compared: 851 cards bought, 48 Prelude Cards kept, 26 Corporations chosen and 3 cards kept of those
  looked at. Switching off the keeps' take-back turns it red.
- **Sampling a sample:** at every Decision of those Games, for every Player, a sample of a sample equals a sample of
  the real Game.
- **Per Decision** (box 2, box 3): the deciding Player's view and Options are the same, every place keeps its count,
  and no card appears twice.
- **The rest:** Draft passes (with the last pass exact more than 100 times), take-backs, seed/log/Replay, the card
  being paid for, and Excentric Sponsor.
- **The handle** (`tests/ai/test_fair_play.py`): handles from a Game and from its sample are equal (view and Decision
  without its sequence) and give equal samples, at every Decision of the 6 fair-play Games. The Sampler offers
  nothing but `sample`.

**The fuzz run** (box 4): `tests/fuzzing/` plays a sample out from about one Decision in 25. It checks the sample's
invariants, view and Options and its fairness (a sample of it against a sample of the real Game), then plays it to
the end with `play_randomly` and checks it again. The full run, on the final code, on mains in the "performance"
profile:

```
uv run python -m tests.fuzzing --games 100000 --first-seed 7000000
100,000 Games and 61,335,879 Decisions in 2852 s (21,505 Decisions per second, checked). The longest Game lasted 35 Generations (the limit is 100).
267 cards were played; never played: none.
No failures.
```

That is about 2.45 million samples played out. Two earlier runs found the two bugs above. Both were stopped, fixed
with regression tests, and run again.

**The benchmark** (box 6), `uv run python -m tools.benchmark --prelude`, on mains, "performance":

```
Making a Sampled Position for the deciding Player (target under 10 µs), and for information, its Sampler:
  at the start (Generation  1):   1.94 µs (met); Sampler   0.95 µs
  halfway      (Generation  7):   2.29 µs (met); Sampler   1.83 µs
  at the end   (Generation 12):   3.08 µs (met); Sampler   2.84 µs
```

A copy takes 0.21 to 0.67 µs, so a sample costs about 4 to 9 copies; a playout from mid-Game takes about 100 µs.
Every handle now makes a Sampler (1 to 3 µs, against a 58 µs pick). The engine played 5,669 Games per second in one
process, against 5,734 in this session before the review's changes. Those are single runs, within about 1%; no
paired comparison was made.

**The cost of playing fair** (box 7). The Flat Playout Bot against itself, fair against cheating, on commit e223d45
plus this work, on mains, "performance", 16 processes, Draft and Prelude:

```
PYTHONPATH=. uv run python .scratch/phase-2-ai-opponent/experiments/cost_of_fair_play.py --games 1000 --first-seed 100 --playouts 20

                                           a: fair         b: cheating
  Win rate                                   46.6%               53.4%
    95% interval                       43.5%–49.6%         50.4%–56.5%
  Wins / draws / losses              465 / 1 / 534       534 / 1 / 465
  Mean Victory Points                         89.7                91.1
  Mean card Victory Points                     7.3                 7.9
  Mean Terraform Rating                       43.4                43.6
Mean Generations: 14.07
Finished: 1,000, stalled: 0, failed: 0.      (514 s)
```

- **Seeds:** the agreed 200 Games, seeds 0 to 99, gave fair 46.5% (39.7–53.4%) in 102 s. That was quick enough to also
  play 1,000 Games on new seeds, 100 to 599, for a tighter interval.
- **The cost:** playing fair costs about 3.4 points of win rate (6.8 between the sides) and 1.4 Victory Points a Game.
  It is real (the interval sits below 50%) but small. With random playouts, knowing the deck and the other hand
  helps little.
- **Seeding:** each Player's random source is `f"{seed}/{player}"`, so the two sides draw the same sample and playout
  seeds in each pair of Games, which reduces noise. It differs from the Match tool's `f"{seed}/{side}/{player}"`, and
  the script saves no Replays of failed Games (none failed).
- **Against the Random Bot**, through the Match tool:
  `uv run python -m ai.match flat_playout random_bot --games 200 --threshold 0.5`. Flat Playout won 200 of 200
  (98.1–100%), 126.6 Victory Points against 53.9 (threshold met).
- **Speed:** one process averages 13.9 ms a pick (median 9 ms, at most 176 ms over 772 picks).

**The GUI.** Browser check at 1440x900:
- The setup screen lists Flat Playout Bot for each Player.
- A Human-against-Flat-Playout-Bot Game, Draft and Prelude, went through setup. The bot chose CrediCor and bought 3 of
  its 10 cards.
- After the Human passed, it played Biofuels and Polar Industries (Ocean on F6) and passed, and Generation 2's Draft
  began.
- There were no console errors.

**Checks:**
- 2,018 tests pass in 62 s.
- `cargo clippy --all-targets` and `cargo fmt --check` are clean, and `npm --prefix gui run build` succeeds.
- On the touched files, `ruff check` finds only the patterns the repo already has: BLE001 on the fuzzer's
  `except BaseException`, now twice, and an old ISC004 in `tools/benchmark.py`. The new files are formatted with
  `ruff format --line-length 120`.
- ADR 0010 gains an amendment: a Sampled Position is the one Game that can't be rebuilt from its Replay. CONTEXT.md's
  Handle and Sampled Position entries and the README are updated.

**The code review against e223d45** (Standards and Spec, in parallel):
- **Fixed:**
  - The unbounded loops in `tests/ai/test_flat_playout.py`, and the formatting.
  - ADR 0010 amended.
  - "copy" no longer describes the Sampler.
  - One wrap-around scan for the Draft and buying.
  - One `readable` helper, and `MAX_PICKS` from `tests/helpers`.
  - Copy and sample timings share `moments` and `microseconds_per_call`, and samples have their own target constant.
  - The KeepCards leak, and the Draft take-back comment.
  - The Draft-pass rules note now says where cards go after buying, and lists unbought passed cards as a limit.
  - Fairness is checked against real positions and in the fuzzer.
- **Left as is:**
  - Card kinds are `usize` constants indexing the pools, not an enum.
  - `Buying.done` and `Drafting.picked` stay two flags.
  - The name `Pin`.
  - "Sampler" isn't a glossary term: it is the engine object, not domain language.
  - "A Decision without its sequence" is written three ways in tests.
  - A Sampler is made for every handle, even for Controllers that never sample.
  - The experiment's seeding, as above.
  - `playing_card`, `deciding`, the 10 µs sample target and the deal-again loop weren't asked for; each is recorded
    above with its reason.

**Open points:**
- A list in the Player View of the cards its Player knows are in the discard pile would close the largest limit.
- The GUI could show `deciding` for another Player ("Player 2 is selling patents").
