# 01 — Prelude cards in the catalog

**What to build:** Import the printed data of Prelude's 47 cards into the card file, so that the catalog, the card gallery and the mismatch report know them, without any Game dealing them yet (ADR 0011).

The saved card list holds them all. Recorded Games confirm which belong: 35 Prelude Cards, 5 Corporations and 7 Project Cards. The card list's other Prelude-marked entries (Corporate Archives, Double Down, Merger, New Partner, Head Start) never appear in those Games and stay out.

- **Prelude Cards:** Acquired Space Agency, Allied Banks, Aquifer Turbines, Biofuels, Biolab, Biosphere Support, Business Empire, Dome Farming, Donation, Early Settlement, Ecology Experts, Excentric Sponsor, Experimental Forest, Galilean Mining, Great Aquifer, Huge Asteroid, Io Research Outpost, Loan, Martian Industries, Metal-Rich Asteroid, Metals Company, Mining Operations, Mohole, Mohole Excavation, Nitrogen Shipment, Orbital Construction Yard, Polar Industries, Power Generation, Research Network, Self-Sufficient Settlement, Smelting Plant, Society Support, Supplier, Supply Drop, UNMI Contractor.
- **Corporations:** Cheung Shing Mars, Point Luna, Robinson Industries, Valley Trust, Vitor.
- **Project Cards:** House Printing, Lava Tube Settlement, Martian Survey, Psychrophiles, Research Coordination, SF Memorial, Space Hotels.

Sources spell some names differently (Allied Bank/Allied Banks, Excentric/Eccentric Sponsor, Biolab/Biolabs). Settle each by the printed card, and record it as ticket 07 of phase 1 did.

**Blocked by:** none

**Status:** ready-for-agent

- [x] The card import brings in exactly these 47 cards, and running it again changes nothing.
- [x] The catalog has a Prelude Card type, and a Game without Prelude never deals any of the 47 cards.
- [x] Each card records its expansion, so that the deck for a Game can be built from it.
- [x] The card gallery draws them, filterable by type, using the card list's layout and icons.
- [x] The mismatch report compares them with the open-source game's definitions, downloading those into `.cache/`, and has no open entries.
- [x] Games without Prelude are unchanged: the benchmark shows no meaningful slowdown, and old Replays load.

## Comments

### 2026-11-06 — implemented (Claude)

**Decisions made with the user:**
- **Phase 2 documents:** committed first, on their own (f575f4e).
- **Downloads:**
  - the open-source game's `src/server/cards/prelude` at the pinned commit (51 files, 57 KB), in `.cache/` and out of git;
  - `images/tags/wild.png` and `images/resources/wild.png` from the card list (14 KB), committed.
  - The saved card list page and its stylesheet were not refreshed.
- **Catalog order:** the new cards go after the base box's, as 7 Project Cards, 5 Corporations and 35 Prelude Cards, so no existing card changes its index. `CardSet` grew from 4 to 5 words now, so that this ticket measures the cost.
- **Coverage check:** it counts only cards with effect data, and names the rest as not implemented.

**Chosen by Claude, on the user's standing instruction:**
- **Names**, also in `docs/rules-notes.md`:
  - **Excentric Sponsor:** a photo of the printed card reads "EXCENTRIC SPONSOR", so this overrides the ticket's "Eccentric" and the id is `excentric_sponsor`. The ticket's list and the spec were corrected.
  - **Allied Banks and Biolab:** no picture of either card could be found. The card list says so, and the open-source game's file names agree, but its display name for the first is "Allied Bank". **Not confirmed by a printed card.**
  - `NAME_CORRECTIONS` also fixes Metal-Rich Asteroid, Psychrophiles, Research Coordination and SF Memorial. Cheung Shing Mars is in title case, though its logo has MARS in capitals.
- **Card file fields:**
  - `"type": "prelude"` for Prelude Cards;
  - a new `"expansion": "base" | "prelude"`, with Corporate Era still its own flag, since those cards are in the base box;
  - `number` stays a number: 1–35 for Prelude Cards and 36–42 for Prelude's Project Cards, printed as #P01–#P42 by `printed_number` (Python) and `printedNumber` (GUI). So two cards can share a number, and only the two together say which card it is.
  - `cost` is null on Prelude Cards, and `"wild"` is a new Tag.

**Design notes:**
- **Import:**
  - A catalog card is one on the page marked base game, Corporate Era, or Prelude without promo, which leaves out the 5 promo cards and Prelude 2.
  - `check_card_set` refuses a page without all 267. `parse_card_list` sorts into catalog order.
  - "Earth Earth" (Space Hotels) is 2 Earth Tags. A Prelude Card has no Requirements; what Ecology Experts draws as one is its effect.
  - `text` now takes a description inside a description (Valley Trust) and leaves out a word drawn as an icon (Vitor's AWARDS). No base card's text changed.
- **Engine:**
  - `PROJECT_CARDS` (208) and `CORPORATIONS` (12) still mean the base box. `BASE_BOX_CARDS`, `PRELUDE_BOX_CARDS` and `CATALOG_CARDS` are new.
  - `find_project_card` and `find_corporation` look only in the base box, so a Scenario can't name a Prelude card, and `deal_corporations` deals only the base box's.
  - `CardType::Prelude`, `Expansion` and `Tag::Wild` are new. `Tag::COUNTED` leaves out wild for now.
- **GUI:**
  - `PrintedCard` draws Prelude Cards. The number's 99 px margin, which the card list sets on each card, is a rule in `cardList.css`.
  - The gallery has a Prelude Card filter and a wild Tag filter, and its search takes "P36".
  - The state editor offers only the base box.
- **Mismatch report:**
  - Project Cards and Prelude Cards pair by printed number, so #P36 never meets #036.
  - It also compares the box a card comes in.
  - **Result: no differences across all 47 cards.** Breaking our data on purpose gives 35 Tag, 7 cost, 3 Victory Point and 3 Requirement differences, so the comparison is real.
  - `NAMES_SETTLED` lists Allied Banks and Excentric Sponsor apart from open names.
  - The 5 new Corporations' starting MegaCredits are under "Not compared" until they have effect data.
  - `--download` skips files already saved.
- **Coverage check:** `is_implemented` is "has effect data". `tests/tools/test_card_coverage.py::test_only_the_prelude_boxs_cards_may_lack_effect_data` pins the exception.

**Checks:**
- **Games unchanged:** 120 Random Bot Games (2–5 Players, Draft on and off, Corporations on and off; 80,090 picks) were saved from the previous commit. Each Replay and each fresh Game with the same seeds gives an identical full view, Decision and game log. Done by a throwaway script, so the suite's own tests are `tests/rules/test_games_without_prelude.py` and the existing Replay tests.
- **Test that can fail:** dealing from the whole catalog makes `test_games_without_prelude.py` fail 5 tests.
- **Speed** (4 alternating rounds of `tools.benchmark --seconds 6` against the previous commit, on battery, power-saver):
  - 5 words with the old iterator were slower in every round: −4.4 % in 1 process, −5.5 % in 16.
  - So `CardSet::iter` became a plain iterator (`CardsInOrder`). With it: 3,950 → 3,908 Games per second in 1 process (−1.1 %), and 7,160 → 7,088 in 16 (−1.0 %). The new code was still a little behind in most rounds, but the rounds overlap. Copies are unchanged: about 0.7 µs at the start, 1.3 µs at the end.
- **Browser, against the live card list page (1440×900):** for all 47 cards, every element's position, size, own text and computed style (images, colours, fonts, filters, shadows, transforms, `::before` on the frame, `::after`) gives the same fingerprint. This found one bug, `.card-corporation` coming before `.resource`, now fixed. The filters (267 in all; 117, 60, 38, 17 and 35 by type), wild Tag, search, click to enlarge and Escape were checked as well. The base box's cards were not compared again, since their rules didn't change.
- **Full run:** 1,774 tests, clippy, `cargo fmt --check`, GUI build. Running the import again leaves the card file byte-for-byte the same.

**Code review** (`/code-review`, standards and spec):
- Fixed:
  - Valley Trust's `text` lost a sentence, and Vitor's had a stray "AWARDS" (spec review).
  - The report's "Names settled by the printed card" overstated the evidence for Allied Banks; it is now "Names settled in the rules notes".
  - Glossary: "Prelude Card" was used for all 47 cards in test names and for the Rust constant, now `PRELUDE_BOX_CARDS`. Bare "logs" and "step" were removed, and the gallery says "Prelude Card".
  - `needs_a_scenario_test` became `is_implemented`. Clearer local names, a flag argument removed from `check_card_set`, a repeated number format, lines over 120 columns, and a stale comment in `PlayerBoards.tsx`.
- Left as is:
  - `PROJECT_CARDS` and `find_project_card` still mean the base box: ticket 02 changes what they mean anyway.
  - `Expansion::Base`, though the base box isn't strictly an expansion.
  - `_number` returns `int | str | None`, mirroring what the open-source files hold.
  - `"effects" in card` written out in three places, the card counts repeated in tests, and the base-box filter in the tests' helpers.
  - `TileFields` still gets the whole catalog, which is harmless while these cards have no effects.
  - **Beyond the ticket text:** the "P36" search, comparing the box a card comes in, the `CardSet::iter` rewrite (needed for the speed criterion) and `--download` skipping saved files.

**Open points:**
- **The user:** if you have the box, check how Allied Banks and Biolab are printed. A different name means changing `NAME_CORRECTIONS` and `NAMES_SETTLED`.
- **Ticket 02:**
  - The deck is still `0..PROJECT_CARDS`, and `Deck` holds `[u8; PROJECT_CARDS]`. Prelude's Project Cards have indices 220–226, which fit a byte, but the array needs 7 more places: 215 cards in all, so the next benchmark should watch that.
  - `played.iter().find(|card| card >= PROJECT_CARDS)` in `game.rs` finds a Player's Corporation, and the line below it their Project Cards. Both are wrong as soon as a Player holds a card past index 208. Check every such range.
  - `tests/helpers.py`'s `PROJECT_CARDS` and `CORPORATIONS`, and the fuzz invariants built on them, mean the base box only.
  - The state editor filters to the base box, in `StateEditor.tsx`.
  - `CARDS_HOLDING_CARD_RESOURCES` has a limit that Psychrophiles may reach.
- **Tickets 03 and 04:**
  - A card must have a scenario test as soon as it gets `"effects"`; the coverage check then fails until it has one. The tests go in `tests/cards/test_<id>.py`.
  - Decide what the wild Tag does. `Tag::COUNTED`, `CountedTag` and `COUNTED_TAGS` leave it out for now. Research Coordination's text says how.
  - `text` keeps the card list's own wording, such as "an Science tag" and "Pay 3 MC .".
- **Ticket 04, Vitor:** the card says 45 MegaCredits, and the open-source game has 48, with the comment "45 + 3 when this corp is played", which is its own effect. The mismatch report will show this once Vitor has effect data, so settle it in the rules notes.
- **Ticket 05:** remove the exception in `test_only_the_prelude_boxs_cards_may_lack_effect_data`, and make `test_every_project_card_of_the_base_box_is_implemented` cover every card. Also, Prelude Cards' own starting MegaCredits (`startingMegacredits` in the open-source files) aren't compared yet.
- **Ticket 08:** the name map needs Allied Bank → Allied Banks. "Excentric Sponsor" needs no entry, assuming the Recorded Games spell it that way as the spec says.
- **Public release** (ADR 0003): the same licence notes as phase 1's ticket 07 apply to the 2 new icons.
- **Status line:** it stays `ready-for-agent`, as on phase 1's tickets.
