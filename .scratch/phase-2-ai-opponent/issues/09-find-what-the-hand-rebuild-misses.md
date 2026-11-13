# 09 — Find what the hand rebuild misses

**What to answer:** Can each Player's hand be rebuilt accurately at every Decision in a Recorded Game, and what does it take?

`experiments/logs_hands2.py` finds 99.5% of played cards in the rebuilt hand without Prelude (98.6% with), but the hand runs about 2 cards too large, and matches the `Hand Counter` tracker at only about 48% of checks after a card is played. In one Game traced by hand it was exact every time the counter refreshed, so the error is uneven and something specific is being missed.

Start by finding Games where the rebuild drifts, and read those moves. Suspects to check, none of them confirmed: Sell Patents wording, discard effects, Research wording in other scraper versions, "cancels their move" lines, the Prelude cases behind that lower 98.6%, and how stale the `Hand Counter` is, since it isn't a perfect reference either.

The answer decides how much Action-phase imitation can use. Some hidden removals may not be named at all, in which case the honest result is a hand with some uncertainty, and that may be good enough.

**Blocked by:** 08 — Recorded Game importer

**Status:** ready-for-agent

- [x] The cause or causes of the drift are found and recorded under Comments, with example Games by table id.
- [x] A rebuild on at least 3,000 Games reports: played cards found, hand size against a reference that was shown to be fresh, and the share of Games with every check exact.
- [x] The result says which Games can be trusted and how to recognise them, and how many Games of each kind that leaves.
- [x] The accuracy needed is decided, with reasons, and tickets 10 and 14 are updated to match.

## Comments

### 2026-11-13 — answered (Claude)

**The answer.** Yes, as to size. Each Player's hand size can be rebuilt at every move: it matches the fresh Hand Counter at 99.19% of 3,758,926 checks, and at every check in 97.2% of the 59,039 kept Games. Which cards the hand holds is known by name for every card that enters, in the 42,431 Games whose versions name both Players' cards. It is not known after a discard the log never names: Sell Patents and Mars University. Such a discard happens in nearly every full Game. Hindsight resolves it, see "The accuracy needed".

`ai/recorded_games/hands.py` (`HandReader`) does it from the slim moves, with 26 tests on hand-written moves, one per trait. `experiments/hands_rebuild.py` and `experiments/hand_counter_freshness.py` measure it on the whole dataset in about 75 s each on all cores. Their per-Game output goes to `.cache/ticket-09/` (gitignored).

**Decisions made with the user** (one opening batch, both recommendations taken):
- The rebuild is code in `ai/recorded_games/` for tickets 10 and 14 to reuse, tested on hand-written log snippets. Diagnosis scripts stay in `experiments/`.
- It reads the dataset's slim moves, not the archive, so it keeps working once the archive is deleted. The archive was read only for its file names, to give table ids (the dataset's Game id is the salted hash of the table id).

**Calls made since** (recommendations, no further questions):
- **The reference.** The reference is the Hand Counter where it has just changed at a move with its own Player's "plays card" line (`CounterCheck`), shown fresh below.
- **Hands with uncertainty.** A hand is the cards named in it, plus `unnamed` cards (entered without a name: the opponent in old logs), minus `gone` cards (left without a name). This is the "hand with some uncertainty" the ticket allowed.
- **`resync`, off by default.** It corrects each hand's size to the counter at each fresh check, counting the difference as unnamed or gone. An error then lasts at most until that Player's next play. Tickets 10 and 14 should use it. Checks are recorded before correcting, so the measurements below are without it unless they say so.
- **Own moves stand in for Decisions.** Action-phase Decisions don't exist until ticket 10, so "at each Decision" below is measured at each Player's own Action-phase moves.

#### Box 1: the causes of the drift, with example Games (table ids)

`logs_hands2.py` ran about 2 cards too large, and matched the counter at only 48% of checks after a card was played. The causes, largest first. Each was found by tracing drifting Games against the counter, and each is now handled and tested.

1. **Discards that never name the card.** Sell Patents ("Player 1 discards 2 card/s (Sell patents)") and Mars University ("discards 1 card/s", or "discards a card") never say which cards. `logs_hands2` removed only named cards, so every such discard left the hand one card too large. This was the main cause of "about 2 cards too large" and of the uneven error: Games without these discards were exact. Examples: 728159988, 608994138. No log names these cards, so after one the hand's size is right but a few named cards may be gone.
2. **Count lines read as card names.** Old wording logs a draw twice: "draws Immigration Shuttles, Big Asteroid, Cupola City | draws 3 cards". `logs_hands2` added "3 cards" as a fourth card. The opponent's draws are count lines only. Names are now paired with the counts of the same kind (draws or keeps) within one Action, across moves (608994138, 513111762).
3. **Plays named only in `card_played`.** At Research Network, Io Research Outpost, Biolabs and Acquired Space Agency, the description shows the draw ("keeps 3 cards: …") and no "plays card" line (750351588). Also, the description's "plays card" line can credit the other Player.
4. **When buying ends.**
   - The Action phase starts at the first move with `card_played`, or an Action `action_type`, or a line only the Action phase has. "skips" is not one: setup logs it.
   - AI Central's draw, logged as "keeps 2 cards" on an `activate_card` move right after the buy, had replaced the buy (750702479, 725484758).
   - A "first action" line after the keep lines in the same move (623296395).
   - Measured: this one change took v2025.10.07.1844 from 86% to 97% of Games with every check exact.
5. **Setup.**
   - The setup keep holds the Corporation and the Prelude Cards. Prelude Cards count in the Hand Counter until played.
   - One version logs the keep as "draws 10 cards: Point Luna, …" (735130649). Another logs it again as a draw (629581645).
   - v2025.08.27 keeps one card at a time, takes a card back with "drafts X", logs "skips rest of actions" during setup, and summarises (460145775).
   - Old logs give only "keeps 5 card/s", plus "You buy"/"You got" lines for the perspective Player. 2 Prelude Cards are added on top (608994138).
   - Glados-version logs deal with "draws 10 cards" (497151787). "takes back their move" repeats the "You buy" lines (564892432).
   - Point Luna's draw at setup is real (623296395).
6. **Looks.**
   - Newer logs mark shown cards with `card_options`. Old ones log them as a draw, recognised by the card and the number shown: Inventors' Guild and Business Network 1, Invention Contest 3 (536691232), Business Contacts 4.
   - Point Luna's one-card draw can come before Business Contacts' four (660758833).
   - Valley Trust's first action shows 3 Prelude Cards and plays one straight from them (670662277, 675368231).
7. **Reveals and other unusual wordings.**
   - Old logs give Acquired Space Agency's and Experimental Forest's cards only as "reveals X: it has a Space/Plant tag" (623296395, 608999238). Search for Life's Microbe card isn't taken.
   - A board bonus draw follows Experimental Forest's reveals (564405014).
   - A play with neither field nor line, here Business Contacts (467618187).
   - "cannot play card Business Empire, player discards it" (683508809).
   - In buying, "drafts X" of a card being kept takes it back (458496814).
8. **Mars University's discard, sometimes dropped.** Newer versions sometimes log only "Player 1 other" and the draw.
   - When that move's reason names Mars University, or Mars University triggered with nothing else that could draw, a one-card draw after it counts as discard-and-draw (756758532, 669517515, 720578876, 632596097, 511291531).
   - With Olympus Conference or Point Luna also triggered, the draws are ambiguous, and inferring there lost more Games than it saved. These are left to `resync` (525727941, 718661090).
9. **Renamed accounts.** In 710 Games, descriptions name a Player by an older account name (679551946). Those lines can't be credited and are counted as `unread`.

The suspects named in the ticket:
- Sell Patents wording is cause 1, and so is Mars University.
- Discard effects: none name cards except the compensation discard in cause 7.
- Research wording in other versions: causes 2, 4 and 5.
- "cancels their move": handled as in ticket 08, and measured. Taking a cancelled buy with no later keep as nothing bought left 54% of Games with every check exact, against 97%. So a buy followed by "cancels their move" stands (now tested).
- The Prelude cases behind 98.6%: setup Prelude Cards, Valley Trust, and plays named only in `card_played`. Prelude Games now do better than Games without it (99.39% against 98.31%).
- The staleness of the counter: see box 2.

Also found: a look flag left over when a look logged no cards. It is now cleared when the next Action starts (found in code review).

#### Box 2: the full run, against a reference shown to be fresh

**The counter is fresh only at its own Player's plays.** `hand_counter_freshness.py`, all 59,039 Games:
- Of the 3,801,258 times a Player's counter changed, 98.89% were at a move with that Player's own "plays card" line. The rebuild agrees with the new value at 99.19% of those.
- The other changes were plays logged only in `card_played` (0.81%; agreement 21%, so stale), other own moves (0.23%) and Tile placements (0.07%).
- Where the counter does not change, the rebuild agrees with it far less often: 22% at the Player's own draws, 50% at activations, 60% at the other Player's moves. The counter simply hasn't refreshed there.
- An unchanged counter at an own "plays card" move agrees 98.0% of the time.
- Before its first change, a counter may read 0 though the Player holds cards (564405014).
- So a check counts only where the counter just changed at its Player's own "plays card" move. At a play that draws (Research), it is compared after the draw, as the counter is.

**The rebuild on all 59,039 kept Games** (`hands_rebuild.py`, `.cache/ticket-09/summary.txt`):

| | Games | Checks exact | Games with every check exact | Plays found by name / as unnamed / missing |
|---|---|---|---|---|
| All | 59,039 | 99.19% (resync 99.90%) | 97.21% | 88.19% / 11.30% / 0.51% |
| Prelude, not conceded | 31,942 | 99.39% | 97.80% | 83.06% / 16.52% / 0.42% |
| Prelude, conceded | 19,480 | 99.26% | 97.46% | 99.47% / 0 / 0.53% |
| No Prelude, not conceded | 5,847 | 98.31% | 94.50% | 80.31% / 18.85% / 0.84% |
| No Prelude, conceded | 1,770 | 97.58% | 92.60% | 99.00% / 0 / 1.00% |

- 351 Games have no check, mostly short conceded ones.
- "As unnamed" are plays in old logs of the opponent's cards, which entered without names. Among Players whose every card entered named (3,771,591 plays), 99.43% were found in the hand by name and 0.57% were missing. That is the figure comparable to `logs_hands2`'s 99.5%. The new rebuild finds as many, without the extra cards.
- By version, the share of Games with every check exact runs from 94.5% (v2025.08.16.0012, v2025.10.07.1547) to 99.7% (old versions). Old versions name few cards, so there is less to get wrong.
- **What remains.** Errors at checks are mostly +1 (14,924 of 30,364): mostly Mars University discards dropped beside Olympus Conference, and renamed accounts. A few Games drift by up to 18. With `resync`, 99.90% of checks agree.

#### Box 3: which Games can be trusted, how to recognise them, and how many

- **Counted:**
  - The Game has at least one check, every check is exact, and `unread` is 0.
  - The hands' sizes are then right at every move, up to an error between two of a Player's plays that the checks never show.
- **Named:**
  - Counted, and no card entered either hand without a name: versions that name both Players' cards (v2025.08.15 on).
  - These are exactly the counted Games with Decision records.
- **Exact:**
  - Named, and no card ever left a hand without a name.
  - Almost only short conceded Games: nearly every full Game has a Sell Patents or Mars University discard.

| | All | Counted | Named | Exact |
|---|---|---|---|---|
| Prelude, all | 51,422 | 49,469 | 37,884 | 2,601 |
| Prelude, not conceded | 31,942 | 30,716 | 19,131 | 131 |
| Prelude, both rated 500+, not conceded | 5,923 | 5,643 | 3,748 | 3 |
| No Prelude, all | 7,617 | 6,896 | 4,547 | 292 |
| No Prelude, not conceded | 5,847 | 5,299 | 2,950 | 39 |
| No Prelude, both rated 450+, not conceded | 770 | 692 | 421 | 2 |

At Players' own Action-phase moves (21,066,663), with resync:
- 49.6% of hands are known card by card;
- 41.4% have every card named, but some may already be sold;
- 9.1% hold unnamed cards (the opponent in old logs).

#### Box 4: the accuracy needed

**Decided, for imitation (ticket 14):**
- Learn the Action phase from **named** Games, read with `resync`: 42,431 Games, of which 22,081 are not conceded. Conceded Games stay usable for Decisions, as the spec says.
- At a Decision, the acting Player's hand must have:
  - its size right at every fresh check of the Game;
  - every card they later play from it present by name. Plays found missing (0.57%) are kept but counted; ticket 10 reports them.
- Cards that left without a name are resolved in hindsight. The sold cards are taken from named cards in the hand that the Player never plays later.
  - That is possible for 98.95% of the 83,171 Players who discarded unnamed. Players for whom it isn't are dropped, or kept with the hand as rebuilt.
  - The only error left is which never-played cards a Player still held at a Decision.
- **Why that is enough:**
  - A model imitates which Option a Player picks. Every card they did play is in the hand.
  - The error is confined to cards that drove no later play, and the hand's size, which the Player View shows the opponent too, stays right.
  - Requiring exact hands would leave 170 Games not conceded, which is far too few.
  - Old-version Games add only one Player's named hand each (11,585 Prelude Games). They are left out at first.

**Decided, for replay through the engine (ticket 10):**
- Replay named Games with `resync`, choosing sold cards in hindsight the same way. Any such choice replays the same, since those cards are never used again; Sell Patents pays 1 M€ for any card.
- Cards that entered unnamed take their names from their plays.
- A "missing" play, a counter mismatch, or an `unread` line is a parser difference group, not an engine bug.

Tickets 10 and 14 now say this.

**Open points:**
- Mars University discards dropped beside Olympus Conference are left to `resync`.
- 710 Games name a renamed account (`unread`). Their slim moves also keep that real account name in descriptions, which ticket 08's "Player names aren't in the dataset" meant to rule out: a follow-up for the importer's anonymiser.
- `HandReader` doesn't yet do the hindsight choice of sold cards. Ticket 10 adds it, as it needs the future moves.

**Code review against 97be385** (Standards and Spec, in parallel):
- **Fixed:**
  - Lines over 120 columns in the format note and the tests.
  - `HandReader.read` was split: a line handler, a Mars University step, and a `MoveReading` for what one move does (this removed the named/counted Data Clump).
  - `Found` and `MarsUniversity` are Literal types.
  - `Keep.take_back` and `Hand.resync` replace reaching into them.
  - A corporation helper replaces three copies; constants come before use; "Action" is capitalised; `Check` became `CounterCheck`.
  - The stale look flag (above).
  - The freshness evidence is now a script on the whole dataset, not a sample.
  - The trust table gained the "exact" column.
  - The cancelled-buy rule was measured and pinned by a test.
- **Left as is:**
  - Strings for line kinds ("draws", "keeps").
  - Named discards ("discards A, B") would be treated as unnamed, but no log has them.
  - "You" lines are credited to the move's Player, which the data bears out.
  - `resync` stays, as tickets 10 and 14 need it.
  - The review's worry that a Player of None reaches `apply_plays` doesn't hold: `slim_moves` drops None values.

**Checks:**
- 2,111 tests pass in 59 s under `timeout`, 26 of them new.
- `uvx --offline ruff check` and `ruff format --line-length 120` are clean on the new files.
- No engine or GUI change.
- The README's "Recorded Games" section and the dataset's format note mention the rebuild.
