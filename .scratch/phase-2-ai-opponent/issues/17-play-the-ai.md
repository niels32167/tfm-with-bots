# 17 — Play the AI

**What to do:** Decide whether phase 2 is finished, by playing the final Controller in the GUI. The goal is that it beats me in most Games with no peeking at hidden cards.

Before playing, fix how many Games count and what result counts, so that the bar can't move afterwards. Ten Games with at least six AI wins is the suggested start, and I choose the final number. The seed of each Game is fixed in advance, and I play as first player in half of them. Use Prelude, Draft and 2 Players, as the AI trained.

If it falls short, look at what beat it (the Replays and its explanations will show where it plays badly) and go back down the ladder. If it gets there, playing further is optional.

**Blocked by:** 16 — Search at play time

**Status:** ready-for-human

- [x] The number of Games and the winning bar are written here before the first Game.
- [ ] Each Game's Replay file is kept and named under Comments, with the result, seed and my notes.
- [ ] Any rule bug gets its own ticket with a Replay and a regression test, and the Game is replayed if it affected the result.
- [ ] I note where the AI played strangely, even in Games it won.
- [ ] The result is recorded, and the README and project status are updated.

## Comments

### 2026-11-24 — the terms, fixed before the first Game

**Chosen by the user:**
- **The bar:** the first 10 Games decide. The AI passes if it wins at least 6 of them. The user plays on for as many
  Games as they can; Games 11 and later are recorded but don't change the result.
- **The AI:** the Search Bot with 5 s per Decision, "Search Bot (5 s)" (`search_5s`), on the registered Value Model
  (`value.pt`, sha256 8bc223e9…, beside `imitation.pt`, 8ae3d240…).
- **Allowed:** advice off; undo as the GUI offers it, which stops at anything hidden. A saved Replay is loaded only to
  go on where a Game stopped, never to go back and pick otherwise.
- **Where:** the live site, https://terraforming-mars-latest.onrender.com, on an image with the 5 s Search Bot.

**Chosen by Claude** (say so before Game 1 to change one):
- **The Games:** 2 Players, Prelude and Draft on, the seeds below in order, each once. The user is always Player 1 and
  the AI Player 2. Who is first Player follows from the seed, and the seeds were drawn so that the user is first in the
  odd-numbered Games (`experiments/17/seeds.py`, which reads only that from each Game, nothing of its deal).
- **A Game counts once its cards are dealt.** One given up counts as an AI win. One lost to a crash or a sleeping server
  goes on from the last saved Replay, repeating the picks made since. If too much is lost to repeat, or nothing was
  saved, it doesn't count, and a reserve seed takes its place, so that nothing seen is played again.
- **A shared win** (tied on Victory Points and on MegaCredits) is no AI win.
- **A rule bug that affected the result:** the Game doesn't count, and a reserve seed takes its place once the bug is
  fixed.
- **A reserve seed** is the first one not yet played of Games 11–30 with the same first Player. Games 11–30 otherwise
  don't count.
- **The bot doesn't change before Game 10 is over:** no new model registered and no new image pushed, except to fix a
  rule bug.

**Before Game 1:** commit, push the image (the user's go-ahead), the user's Manual Deploy on Render, and a check that
the live site offers "Search Bot (5 s)".

**Keeping the Replay:** at the end of each Game, **Save Replay**, and the file goes into
`.scratch/phase-2-ai-opponent/play-test/`. Saving once each Generation is the way back if the server sleeps.

| Game | Seed | First Player | Winner | Victory Points (me – AI) | Replay file | Notes, strange AI play |
| ---: | ---: | --- | --- | --- | --- | --- |
| 1 | 474875664 | me | | | | |
| 2 | 594227686 | AI | | | | |
| 3 | 794176515 | me | | | | |
| 4 | 737566236 | AI | | | | |
| 5 | 497598364 | me | | | | |
| 6 | 65423259 | AI | | | | |
| 7 | 526531672 | me | | | | |
| 8 | 20576357 | AI | | | | |
| 9 | 266034153 | me | | | | |
| 10 | 938387620 | AI | | | | |

Reserves and further Games, which count only in another's place:

| Game | Seed | First Player | Winner | Victory Points (me – AI) | Replay file | Notes, strange AI play |
| ---: | ---: | --- | --- | --- | --- | --- |
| 11 | 694429324 | me | | | | |
| 12 | 705962174 | AI | | | | |
| 13 | 52061127 | me | | | | |
| 14 | 631010901 | AI | | | | |
| 15 | 652341007 | me | | | | |
| 16 | 999292662 | AI | | | | |
| 17 | 89983528 | me | | | | |
| 18 | 408333771 | AI | | | | |
| 19 | 798809429 | me | | | | |
| 20 | 868073858 | AI | | | | |
| 21 | 273761780 | me | | | | |
| 22 | 727038069 | AI | | | | |
| 23 | 21191087 | me | | | | |
| 24 | 972295694 | AI | | | | |
| 25 | 506683337 | me | | | | |
| 26 | 371632633 | AI | | | | |
| 27 | 601494100 | me | | | | |
| 28 | 197748262 | AI | | | | |
| 29 | 304524919 | me | | | | |
| 30 | 151918092 | AI | | | | |

### 2026-11-24 — why 5 s: what the live site leaves of the Search Bot (Claude)

The user first chose the Search Bot at 1 s, played on the live site. Render's free instance has a tenth of a core, so
this was measured before the first Game, on the laptop (mains, "performance" profile) with and without `CPUQuota=10%`,
on every third Decision searched in one Game of the Imitation Bot's, 45 in all (`experiments/17/samples_at_a_tenth.py`,
`.cache/ticket-17/samples-*.txt`):

| CPU and budget | Sampled Positions per Decision searched: median (quartiles) | Seconds per pick: median (most) |
| --- | --- | --- |
| a whole core, 1 s | 14 (11–22) | 0.94 (0.99) |
| a tenth, 1 s | 2 (2–3), and only 1 in 20% | 0.80 (1.00) |
| a tenth, 5 s | 7 (6–12) | 4.4 (5.1) |

Render's cores may be slower than the laptop's, so these are the most to expect there.

**At 2 Sampled Positions the Search Bot only equals the registered Value Bot:** 50.2% (45.4–55.1%) of 400 Games on
seeds 3,500,000–3,500,199 (201 to 199, Victory Points 90.2 – 90.4, none stalled;
`.cache/ticket-17/match-search-2-samples-vs-value.txt`). Told this, the user gave it 5 s rather than playing locally.
The Search Bot with 5 s at a tenth of a core hasn't played the Value Bot.

**The code:** `search_5s`, a registered Controller of its own, since a hosted server refuses settings after a name. The
Replay file then names it. Test: `tests/ai/test_search.py`.

**Checked on the live site,** on seed 1, not one of the counted: with the 1 s Search Bot (the image doesn't hold the 5 s one yet): the seed field, the bot as Player 2 and the first
Player (the AI, as the engine says) come out right, and a Replay saved there loads again unchanged.

**Checked at a tenth of a core,** the hosted server on the laptop (`CPUQuota=10%`, 512 MB) against `search_5s`, random
picks for 200 s: 97 picks, into Generation 9. The setup screen's list has "Search Bot (5 s)", the longest wait for one
pick was 5.0 s, and memory peaked at 388 MB.

**Open point:** ADR 0013 has a Controller move up only by winning a Match. The 1 s Search Bot did, on a whole core. The
bot these Games are against, 5 s at Render's share, has played no Match; the user chose it knowing that.

**Code review** (`/code-review` against 1ef8295, one standards and one spec subagent, read-only). Fixed: the crash rule
let cards already seen be played again; which of Games 11–30 may count; laptop figures stated as Render's; the 1 s
figures in ADR 0014 unlabelled; the setup screen's strength claim; the experiment script. Left as is: `search_5s`
repeats `search`'s registry fields, as the Imitation Bots do; no server test of its own, since the hosted server offers
whatever is registered (`tests/server/test_hosting.py`).
