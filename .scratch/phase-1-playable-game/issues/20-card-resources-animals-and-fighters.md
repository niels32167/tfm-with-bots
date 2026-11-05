# 20 — Card Resources: animals and fighters

**What to build:** Cards that use animal or fighter Card Resources, including protection effects and the cards that remove animals from other Players.

Every card in this batch works exactly as printed, following the rules authority order (rulebook, then official FAQ, then the open-source game). Simple effects go in the card's effect data; triggers, ongoing effects, actions and unusual cards get Rust code (ADR 0009).

If a card turns out to need machinery from another ticket, move it to that ticket and note the move in both.

**Blocked by:** 15 — Active cards with actions; 16 — Ongoing effects; 17 — Attacks

**Status:** ready-for-agent

- [x] Every card below has at least one scenario test through the Python engine module, covering its Requirements, its effect and its Victory Points.
- [x] This batch's entries in the card mismatch report (ticket 07) are resolved.
- [x] Rules judgment calls are recorded in the rules notes.
- [x] Every card is playable in the GUI, and the short fuzz run stays clean with these cards in the deck.

**Cards in this batch (17):**

CEO's Favorite Project (#149, ticket 19, moved from ticket 14) adds 1 Card Resource to any card with at least 1: check that it can target this batch's animal and fighter cards too.

Ticket 19's machinery (see "Card Resources", "An action's alternatives" and "Adding Card Resources to another card" in docs/rules-notes.md): `"holds"`, `"card_resources"`, `"add_to_another"`, a Trigger's `"card_resources"`, `{"tag_played": [...]}` and an action's `"choice"`. Add this batch's 9 cards that hold some to `CARDS_HOLDING_CARD_RESOURCES` in `tests/helpers.py` (the Game has room for all 18: `card_resources::CARDS_HOLDING_CARD_RESOURCES`) and those that add to another to `ADDING_TO_ANOTHER_CARD` in `tests/fuzzing/invariants.py`. `"choice"` is only for an action so far: Imported Hydrogen, Large Convoy and Local Heat Trapping need it when played (`Card::action_alternative`, `action_alternatives`). `tests/cards/test_decomposers.py` checks an animal Tag only through Advanced Ecosystems: add a test with one of this batch's animal cards.

- [x] #019 Imported Hydrogen
- [x] #024 Predators — "remove 1 animal from any card" is `"action": {"any_player": {"move_card_resource": "animal"}}`, as Ants (ticket 19), which takes from the opponents' cards first and has no "Remove nothing": see "Ants" in docs/rules-notes.md. Add it to `MOVING_A_CARD_RESOURCE` in `tests/fuzzing/invariants.py`
- [x] #026 Eos Chasma National Park
- [x] #028 Security Fleet
- [x] #050 Virus — "remove up to 2 animals or 5 plants from any player" is ticket 17's `"any_player": {"remove": [...]}` once a Card Resource can be an alternative
- [x] #052 Fish
- [x] #054 Small Animals
- [x] #072 Birds
- [x] #074 Viral Enhancers — the open-source game offers Nitrophilic Moss (ticket 13, "lose 2 plants") with only 1 plant while Viral Enhancers is in play, as its plant Tag gains a plant first; Moss (#122, lose 1) likewise with none. Decide whether the plant loss is checked before or after the "when you play" effect, and update "Production at its limit" in docs/rules-notes.md
- [x] #128 Ecological Zone — a `"when"` Trigger (ticket 16) on several Tags with a Card Resource gain, as Decomposers (ticket 19): `{"on": {"tag_played": ["animal", "plant"]}, "card_resources": 1}`. Its Tile is a special Tile (ticket 18): add `SpecialTile::EcologicalZone` in `engine/src/board.rs` (the catalog checks its card index) and its symbol in `gui/src/components/MarsBoard.tsx`'s `SPECIAL_SYMBOLS`, and give it a placement rule as an `Areas` value ("adjacent to any greenery tile"), also written out in the fuzzer's `legal_areas`
- [x] #143 Large Convoy
- [x] #147 Herbivores — a `"when"` Trigger (ticket 16): `{"tile_placed": {"tile": "greenery", "by": "you"}}`, with a Card Resource gain
- [x] #163 Imported Nitrogen
- [x] #172 Pets — a `"when"` Trigger (ticket 16): `{"tile_placed": {"tile": "city", "by": "anyone"}}`, with a Card Resource gain. The printed card says "Animals may not be removed from this card", which `cards.json`'s text leaves out (the open-source `Pets.ts` has it as `protectedResources`): `targets::cards_with_some` must leave Pets out for Predators, and Virus must too
- [x] #173 Protected Habitats — "opponents may not remove your plants, animals or microbes": `targets::target_options` must leave its Player out of plant removals (Asteroid, Comet, Big Asteroid, Deimos Down, Mining Expedition, Giant Ice Asteroid, ticket 17), `targets::cards_to_take_from` must leave their cards out for Ants (ticket 19) and Predators, and the fuzz invariant `targets_offered_are_those_the_rules_allow` must know it. It doesn't protect Production
- [x] #184 Livestock
- [x] #190 Local Heat Trapping

## Comments

### 2026-11-05 — implemented (Claude)

**Decisions made with the user:** none. The ticket's calls were to be made without a question batch, as on ticket 19, so every call below is Claude's recommended one (recorded in `docs/rules-notes.md` under "Effects chosen when a card is played", "Predators", "Virus", "Pets and Protected Habitats", "Viral Enhancers", "Ecological Zone" and "Production at its limit"). Test seams are the ones agreed on tickets 11–19.

**Calls made by Claude:**
- **Viral Enhancers' plant comes before a card's plant loss.** Moss is offered with no plant while it is in play, and Nitrophilic Moss with 1. The rulebook: "These effects (and other effects triggered by the card you just played) are performed in any order you choose", gaining first is never worse, and the open-source game's two `bespokeCanPlay`s say the same.
- **Viral Enhancers' Decision comes last, with no Decision about its order.** Checked against Olympus Conference and Mars University, as GHG Producing Bacteria sets off all three: the plant or Card Resource changes nothing for them, and a card they draw may show which to take, so last is never worse. A card that holds none gains its plants at once, with no Decision.
- **Virus takes all its animals from one card.** The rulebook says "All removed resources must come from the same player" but not one card; the FAQ can't be fetched, and the open-source game's `RemoveResourcesFromCard` picks one card. The printed text could also allow 1 each from two of a Player's cards, so this is worth a look in the play-test.
- **Virus never offers the Player's own animals or plants** (the open-source game does), as removing nothing is never worse: "Taking from any Player" already leaves their own Resources out.
- **Imported Hydrogen, Large Convoy and Local Heat Trapping choose after their Ocean**, as its placement bonus may draw a card that decides the choice, and adding is offered only with a card for it. This follows the ticket's "fit it into the flow", but after `place_card_tiles`, not before: `offer_alternatives` in `finish_unless_placing`.
- **Pets protects against its own Player too** ("may not be removed"; `protectedResources` in the open-source game). With animals only on Pets, Predators isn't offered.
- **Protected Habitats:** with every opponent protected, Predators and Ants turn to the Player's own cards, as they do when no opponent has any. It protects no Production, and no MegaCredits, steel or titanium.
- **Predators' move back onto itself stays offered**, as a no-op action isn't dominated (ticket 19's spec review).
- **Ecological Zone's Tile goes next to any Greenery**, whoever owns it, though the Requirement needs one of the Player's own, as printed and in the open-source game.
- The *Comprehensive FAQ* could not be checked (the PDF and BoardGameGeek refuse the download). The rulebook wording comes from rulespal.com's copy.

**Design notes:**
- **Effect data** (`engine/cards/cards.json`): the 17 cards. All 208 Project Cards are now implemented: 112 Automated, 59 Active and 37 Events (the README says so). New forms: `"choice"` on a card when played, `{"card_resource": "animal", "amount": 2}` as an alternative of `"remove"` (`cards::Removal`), and `{"tile": "special", "on": "next_to_a_greenery"}`. Rust code only for Pets, Protected Habitats and Viral Enhancers (`card_code`).
- **Engine:**
  - `card_actions.rs`: `alternatives`, `alternative_options` and `carry_out_alternative` now serve a card as well as an action; `offer_alternatives` is the played card's Decision (`Game::choosing_for`). `Card::alternatives` reads `"choice"` from either place, as no card has both.
  - `targets.rs`: `cards_to_remove_from(owner, kind, by)` knows Pets and Protected Habitats; `removable_from_opponent` leaves protected plants out; `DecisionOption::RemoveFromCard` for Virus.
  - `card_code.rs`: `ViralEnhancing` (`Game::viral_enhancing`, the card played and how many Tags are left), `offer_viral_enhancers`, `plants_from_viral_enhancers`.
  - `triggers.rs`: `set_off` matches on the card, with Viral Enhancers' Decision only for a card played that holds some. Otherwise its data's plant is gained.
  - `playing_cards.rs`: `can_carry_out_with_plants` for the plant check.
  - `board.rs`: `SpecialTile::EcologicalZone`, `Areas::NextToAGreenery`.
- **GUI:** the paw in `MarsBoard.tsx`, status text for the new Decisions and `PICKED_ON_A_CARD`'s `remove_card_resources` for Virus. Badges worked without a change, the fighter icon included.
- **`engine/tm_engine.pyi`** documents all of it.
- **Tests** (1,529 in all, up from 1,363): 17 card files, each with its Requirements, effect, Victory Points and the ticket's notes; `tests/cards/test_decomposers.py` with a real animal card; `tests/cards/test_ceos_favorite_project.py` targeting animal and fighter cards; `PRINTED_VICTORY_POINTS` with the 9 new holders; `tests/server/test_card_resources.py` with the three new Decision shapes; `test_every_project_card_is_implemented` replaces the test that used Birds as not implemented.
- **Fuzzer:** `ADDING_TO_ANOTHER_CARD`, `MOVING_A_CARD_RESOURCE`, `PRODUCTION_TAKEN`, `RESOURCES_TAKEN` and `CARDS_HOLDING_CARD_RESOURCES` extended; new `CARD_RESOURCES_TAKEN`, `ALTERNATIVES_WHEN_PLAYED`, `cards_to_remove_from` and `viral_enhancers_offers_what_the_card_says`; `targets_offered_are_those_the_rules_allow` knows Protected Habitats and Pets, `effects_offered_are_those_the_rules_allow` knows played cards, and `legal_areas` and `special_tiles_where_their_cards_put_them` know Ecological Zone, each with a test that breaks it.
- **In 300 random Games with the implemented cards first** (2–5 Players), the cards were played: Virus 116, Protected Habitats 94, Security Fleet 80, Viral Enhancers 78, Pets 68, Imported Hydrogen 66, Local Heat Trapping 61, Imported Nitrogen 47, Eos Chasma National Park 36, Ecological Zone 33, Small Animals 33, Herbivores 27, Large Convoy 25, Fish 22, Predators 14, Birds 9, Livestock 7. Actions used: Security Fleet 88, Small Animals 73, Fish 49, Predators 8, Livestock 7, Birds 5. There were 357 "effects" Decisions (18 of them for a card played), 14 "add_to_card", 30 "viral_enhancers" and 767 "target". 2,103 Card Resources lay on cards at the end.
- **Checked in the browser** (1440×900, Hotseat, a Scenario loaded through a second WebSocket): Ecological Zone played from the hand dock, placed next to a Greenery, and asked twice by Viral Enhancers; its paw shows on the Tile; Virus' Options leave Pets out, and clicking an outlined Small Animals removed 2 animals; Predators' Options leave Pets out; Security Fleet's action; Imported Hydrogen's Ocean, then its choice, then the card to add to, with buttons and outlined cards. Badges show animals and fighters. The only console error is the known `@vite/client` `ERR_BLOCKED_BY_CLIENT`. The review's fixes after this changed no GUI file or Decision, so the browser check wasn't repeated. Local Heat Trapping, Large Convoy and the rest share these Decisions.
- **Game length and speed** (2026-11-05, on battery, discharging from 61 % to 34 %, "performance" profile, with the three variants measured one after the other):
  - Fuzzing: 20,000 Games with 2–5 Players and 13,978,975 Decisions in 345 s, then after the code review's fixes another 20,000 (13,974,118 Decisions, 337 s), each clean, the longest Game 34 Generations.
  - Benchmark: 5,802 Games/s in 1 process and 57,506 on 16, against 5,926 and 59,410 for da8c53f measured the same way. Measured as this engine with the new cards' data left out, in identical Games (682 picks): 5,827 and 59,129, so the code costs about 0.5–2 % and the rest is the 17 new cards. Copies take 0.21 µs at the start of a Game (measured before the review's fixes) and 0.96 µs at its end. Every target is met.
- **Card mismatch report:** 0 differences.

**Code review** (`/code-review`, standards and spec; no bug in real play found):
- Fixed:
  - `Removal` lacked `deny_unknown_fields`, against the README's "allows no unknown field".
  - Names: `cards_with_some` no longer meant what it said, and with `cards_an_opponent_may_take_from` it became `cards_to_remove_from(owner, kind, by)`, which also removes a constant `.filter`; `plants_on_playing` became `plants_from_viral_enhancers` and now reads the data's plant amount; a stale test name.
  - `set_off`'s awkward `else if let` tuple became a `match`, and a `u32` that could underflow on `None` an `expect`.
  - The `add_to_card` invariant now finds the addition by the Options' kind, so it catches Imported Nitrogen's animals offered at the microbes' amount.
  - Doc comments: the `card_actions` module's, and long lines. A garden-path README sentence, and a cryptic test literal.
  - Tests for Pets on a City off Mars, Herbivores in the final Greenery conversion, Ecological Zone in `test_reserved_areas.py`, and 0 Victory Points on the five cards without any.
- Left as is:
  - **`Steal(Vec<Removal>)`** though no card steals from a card: it lets `Remove | Steal` share `target_options` and `taking`. Its doc comment says so.
  - **`offer_alternatives` and `choose_action_alternative` both match on `alternative_options`**: they go on differently, one ending an action and the other falling through to what is due.
  - **`can_carry_out` only delegates to `can_carry_out_with_plants`**: every other caller has no plant to count.
  - **Played-or-action decided in `Card::alternatives`, `carry_out_alternative` and `StatusBar`**, on the doc's "No card has both": no such card in v1.
  - **The status bar's repeated card lookups, the server tests' `scenario`/`file` boilerplate and each new Decision touching `game.rs`, `view.rs`, the `.pyi` and `StatusBar`**: the surrounding code's pattern.
  - **`DecisionOption::RemoveFromCard`'s `(owner, from)`** follows `MoveCardResource`.

**Open points:**
- **Virus and two cards:** see the call above, for the play-test (ticket 25).
- **Hand-offs:** ticket 21 (Helion's heat and Local Heat Trapping; a Corporation's Tags and Triggers), ticket 23 (the paw draws from a colour emoji font, unlike the other symbols), ticket 24 (`implemented_cards_first` changes nothing now: decide whether to remove it).
- **Still open from earlier tickets:** Scenarios refuse an Ocean on land and don't keep Cities apart (ticket 22); `CARDS_WITH` covers only Project Cards (ticket 21); "target", "taking", "Trigger", "Discount", "claim" and "alternative" are not in `CONTEXT.md`, a gap to settle with `/domain-modeling`. Ticket 22's state editor can't set Card Resources yet.
- **Status line:** it stays `ready-for-agent`, because `docs/agents/triage-labels.md` has no "done" label.
