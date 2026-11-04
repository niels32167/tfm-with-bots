# 19 — Card Resources: microbes and science

**What to build:** Cards that use microbe or science Card Resources. This brings in Card Resources: adding them to and removing them from cards, and Victory Points per Card Resource. The GUI shows Card Resources on played cards.

Every card in this batch works exactly as printed, following the rules authority order (rulebook, then official FAQ, then the open-source game). Simple effects go in the card's effect data; triggers, ongoing effects, actions and unusual cards get Rust code (ADR 0009).

If a card turns out to need machinery from another ticket, move it to that ticket and note the move in both.

**Blocked by:** 15 — Active cards with actions; 16 — Ongoing effects

**Status:** ready-for-agent

- [x] Every card below has at least one scenario test through the Python engine module, covering its Requirements, its effect and its Victory Points.
- [x] This batch's entries in the card mismatch report (ticket 07) are resolved.
- [x] Rules judgment calls are recorded in the rules notes.
- [x] Every card is playable in the GUI, and the short fuzz run stays clean with these cards in the deck.
- [x] Test: Card Resources count for Victory Points as printed.

**Cards in this batch (13):**

- [x] #005 Search for Life
- [x] #033 Regolith Eaters
- [x] #034 GHG Producing Bacteria
- [x] #035 Ants — "remove 1 microbe from any card" can share ticket 17's target Decision (`Waiting::Target`, `targets::target_options`; "Remove nothing" offered, never the Player's own cards while that only does worse): see "Taking from any Player" in docs/rules-notes.md. "Remove nothing" is not offered, against this note: see "Ants" in docs/rules-notes.md and the Comments
- [x] #049 Tardigrades
- [x] #095 Physics Complex
- [x] #131 Decomposers — a Trigger in ticket 16's `"when"` form, but `{"tag_played": ...}` takes one Tag and a Trigger gains only Resources and Production: extend both (several Tags, a Card Resource gain), and the card's "including this" makes its own Tags count, as Mars University's do
- [x] #133 Symbiotic Fungus
- [x] #134 Extreme-Cold Fungus
- [x] #149 CEO's Favorite Project — moved here from ticket 14 (2026-10-29): an Event that adds 1 Card Resource of any kind to a card with at least 1 on it; ticket 20 adds animals and fighters to what it can target
- [x] #157 Nitrite Reducing Bacteria
- [x] #170 Aerobraked Ammonia Asteroid
- [x] #185 Olympus Conference — Research (ticket 12) counts as playing 2 science Tags, so it triggers this twice. A `{"tag_played": "science"}` Trigger like Mars University's (ticket 16), with a Decision of its own: with both in play, the two are due on the same science Tag, so order them by the simultaneous-effects rule ("When the 0 °C Ocean is placed" in docs/rules-notes.md), asking the user if no order dominates

## Comments

### 2026-11-04 — implemented (Claude)

**Decisions made with the user:** none. The user asked to be kept out of the loop on this ticket, so
no question batch was asked, and every call below is Claude's recommended one (recorded in
`docs/rules-notes.md` under "Card Resources", "An action's alternatives", "Adding Card Resources to
another card", "Ants", "Decomposers", "Search for Life" and "Olympus Conference and Mars University").
Test seams are the ones agreed on tickets 11–18.

**Calls made by Claude:**
- **Ants has no "Remove nothing", against this ticket's note.** The rulebook: "When you use an action
  on a blue card, you must first pay any cost stated to the left of the arrow", and Ants' microbe is
  there. The open-source game's removal is mandatory for a cost too. So the action moves a microbe
  or isn't used. Opponents' cards come first, as the note asks; once no opponent has a microbe, the
  Player's own cards are offered, Ants itself included ("any card").
- **Olympus Conference and Mars University: no order dominates, so the Player orders them.** Discarding
  first lets them see the card and still keep their science; removing first lets them see the card
  and then choose the discard. The ticket said to ask the user here; the user's instruction covers it.
  One "olympus_conference" Decision offers both cards' Options, the one picked is carried out and the
  rest stay due, so no separate "which first" Decision is needed. Adding to an empty Olympus Conference
  is never worse first, so it comes without a Decision, and with an empty hand Olympus Conference comes
  first. The open-source game fixes Olympus Conference first.
- **Symbiotic Fungus's action with no card to add to is offered and does nothing**, and so is Ants moving a
  microbe back onto itself. The rulebook doesn't speak of this for actions, so the open-source game
  decides. These first went the other way, and the spec review caught it: an action that changes nothing
  keeps its Player in the Generation, so it isn't dominated.
- **Aerobraked Ammonia Asteroid can be played with no card for its microbes**, which are lost (the
  rulebook's own exception). **CEO's Favorite Project can't** ("a card with at least 1"), as the
  open-source game's `mustHaveCard`. It adds to the Player's own cards only.
- **Removing Card Resources at a Global Parameter's maximum is still offered**, as with Asteroid.
- **Search for Life's reveal is public**: the log names the card, which then goes to the discard pile.
  The action isn't offered with no card left to reveal.
- **GUI:** a badge with the Card Resource's icon and count on each played card that holds some, 0 too,
  next to the cost, where it stays in view when the cards overlap. The cards a Decision offers to give or
  take are outlined and clickable, and are status-bar buttons as well, since the played cards may be out
  of view when a choice is required.
- The *Comprehensive FAQ* could not be checked (the PDF and BoardGameGeek refuse the download). The rulebook
  wording comes from rulespal.com's copy.

**Design notes:**
- **Effect data** (`engine/cards/cards.json`): the 13 cards. 191 cards are now implemented: 111
  Automated, 48 Active and 32 Events (the README says so). New fields: `"holds"`, `"card_resources"`,
  `"add_to_another"` (`{"kind", "amount", "at_least", "must_have_card"}`), an action's `"choice"`, a
  Trigger's `"card_resources"`, `{"tag_played": [...]}` (now a list, Mars University's too) and
  `"any_player": {"move_card_resource": "microbe"}`. Only Search for Life and Olympus Conference have Rust
  code (`card_code`).
- **Engine:**
  - `card_resources.rs`: `CardResources`, a `[u16; 18]` on the Game with a slot per card that holds them
    (`CardSet::rank` finds it), so copies stay plain; `Adding`, a `&'static` slice of what is still to add;
    the "add_to_card" Decision.
  - `card_actions.rs`: `action_alternatives` and the "effects" Decision (`DecisionOption::ChooseEffects`,
    `Waiting::Effects`).
  - `targets.rs`: `AnyPlayer::MoveCardResource`, `cards_to_take_from`, `DecisionOption::MoveCardResource`.
    `any_player` looks at a card's action too.
  - `card_code.rs`: `search_for_life`; `offer_science_tag_effects` replaces `offer_discard_to_draw`;
    `olympus_conference_options`.
  - `playing_cards.rs`: `carry_out` takes the card, and `count_for_card` counts Card Resources.
  - `triggers.rs`: several Tags, a Card Resource gain, Olympus Conference's due count.
  - Scenarios take a Player's `"card_resources"`; the view has each board's `"card_resources"`.
- **GUI:** `PlayedCards.tsx` (badges, `PICKED_ON_A_CARD`, the action under way stays outlined) and
  `StatusBar.tsx` (status text for the new Decisions).
- **`engine/tm_engine.pyi`** documents all of it.
- **Tests** (1,363 in all, up from 1,249): 13 card files, each card's ticket note among them (Research sets off
  Olympus Conference twice; Decomposers' own Tag counts; both orders with Mars University);
  `tests/rules/test_card_resources.py` with the done criterion's
  `test_card_resources_count_for_victory_points_as_printed`; `tests/server/test_card_resources.py` for the
  new Decisions over the WebSocket; `CARDS_HOLDING_CARD_RESOURCES` in `tests/helpers.py` is the printed list.
- **Fuzzer:** `card_victory_points` counts the real Card Resources; `targets_offered_are_those_the_rules_allow`
  knows Ants; new invariants `card_resources_only_on_played_cards_that_hold_them`,
  `card_resource_actions_can_be_carried_out`, `cards_to_add_to_are_those_the_rules_allow`,
  `effects_offered_are_those_the_rules_allow` and `olympus_conference_offers_what_the_card_says`, each with
  a test that breaks it.
- **In 300 random Games with the implemented cards first** (2–5 Players), the cards were played: Tardigrades
  108, Olympus Conference 92, Physics Complex 89, Search for Life 82, Symbiotic Fungus 76, Nitrite Reducing
  Bacteria 65, Regolith Eaters 62, Decomposers 52, Aerobraked Ammonia Asteroid 51, GHG Producing Bacteria 48,
  Ants 45, Extreme-Cold Fungus 29, CEO's Favorite Project 19. Actions used: Tardigrades 598, Search for Life
  514, Nitrite Reducing Bacteria 291, Regolith Eaters 273, Symbiotic Fungus 227, Extreme-Cold Fungus 189, GHG
  Producing Bacteria 134, Physics Complex 86, Ants 84. There were 332 "effects" Decisions, 8 "add_to_card", 21 picks of a
  card for Ants and 65 "olympus_conference" (7 of them answered with Mars University first). 1,352 Card Resources lay on cards
  at the end.
- **Checked in the browser** (1440×900, Hotseat, Scenarios loaded through a second WebSocket): the cards played
  from the hand dock and their actions from the played cards; a badge on each card holding Card Resources;
  each new Decision's status text and buttons; clicking an outlined played card picks it, an opponent's too;
  Research with both cards in play, in both orders. No console errors. After the review's fixes, Ants was
  checked again.
- **Game length and speed** (2026-11-04, on mains but "not charging" at 80 %, "performance" profile):
  - Fuzzing: 20,000 Games with 2–5 Players and 13,910,123 Decisions in 327 s, with no failures, the longest
    Game 34 Generations. After the code review's fixes, another 20,000 (13,932,588 Decisions, 320 s, longest
    35 Generations) were also clean.
  - Benchmark: 5,839 Games/s in 1 process and 60,988 on 16, against 6,330 and 62,966 for 703c39c measured the
    same day. Measured as this engine with the new cards' data removed, in identical Games (751 picks): 6,213
    against 6,330 on 1 process and 62,224 against 62,966 on 16, so the code costs about 1–2 % and the rest is
    the 13 new cards. Copies take 0.21 and 0.98 µs. Every target is met.
- **Card mismatch report:** 0 differences. Search for Life stays under "Not compared", as the open-source game
  works out its Victory Points in code; its test covers them.

**Code review** (`/code-review`, standards and spec; no bug in real play found):
- Fixed:
  - Glossary: "resource" on its own became `kind` (the data's `"kind"`, the details' `"kind"`), and a local
    `choice` holding Options became `own_options`.
  - The spec review's Symbiotic Fungus and Ants-itself finding (above), and a wrong clause in the Ants note.
  - `on` is safe for a card holding none, as a Scenario's unimplemented Birds read another card's slot.
  - One name for the move (`MoveCardResource`, details `"move_card_resource"`); `CARDS_HOLDING_THEM` renamed;
    `AddToAnother::amount_text`, `Card::held` and `Player::cards_holding_card_resources` replace repeats; `science`
    dropped from Olympus Conference's details, as `draw` says it; no `Vec` to test whether Ants can act; two
    wrong doc comments and a 170-column one.
  - Server tests for the three other new Decisions; ticket 20 now says Pets' Animals can't be removed.
- Left as is:
  - **`Effects.choice`**, though the glossary avoids "choice" for an Option: it follows `resources_choice`.
  - **`resources_choice` and `choice` both exist**: replacing the first means moving Electro Catapult and
    its details to the second, for no gain here.
  - **`AnyPlayer::MoveCardResource` panics in `taking`**: it shares the target Decision as the ticket asks,
    but takes from a card, so `taking` doesn't apply.
  - **`Vec<(usize, usize)>` in `cards_to_take_from`**: used in one place, with a doc comment.
  - **`cardResourcesText` in the GUI repeats `CardResource::counted`**: the view sends amounts, not text.
  - **The status bar's repeated card lookups and the invariants' one-card guards**: the surrounding code's pattern.
  - **Clickable played cards go beyond "shows Card Resources"**: a call recorded above.

**Open points:**
- **Hand-offs on ticket 20:** the machinery and lists to extend; `"choice"` when a card is played (Imported
  Hydrogen, Large Convoy, Local Heat Trapping); Predators as Ants; Protected Habitats and Pets in
  `cards_to_take_from`/`cards_with_some`; an animal-Tag test for Decomposers with a real animal card.
- **Still open from earlier tickets:** Scenarios refuse an Ocean on land and don't keep Cities apart
  (ticket 22); Viral Enhancers' plant check (ticket 20); `CARDS_WITH` covers only Project Cards (ticket 21);
  "target", "taking", "Trigger", "Discount", "claim" and now "alternative" are not in `CONTEXT.md`, a gap to
  settle with `/domain-modeling`. Ticket 22's state editor can't set Card Resources yet.
- **Status line:** it stays `ready-for-agent`, because `docs/agents/triage-labels.md` has no "done" label.
