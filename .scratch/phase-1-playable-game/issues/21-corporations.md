# 21 — Corporations

**What to build:** At setup each Player is dealt two Corporations, picks one, and starts with its starting MegaCredits and other Resources and Production. This replaces the temporary fixed amount used so far. The choice is taken one Player at a time and stays hidden until it is revealed as the rules say.

All 12 Corporations work as printed:
- Credicor, Ecoline, Helion, Interplanetary Cinematics, Inventrix, Mining Guild, Phobolog, Tharsis Republic, Thorgate and United Nations Mars Initiative;
- the Corporate Era Saturn Systems and Teractor.

Their abilities reuse the action, trigger, discount and payment machinery. For example, Helion lets heat pay as MegaCredits.

The Beginner Corporation is left out: it isn't on the card list, and it belongs to the beginner variant, not the Corporate Era game.

**Blocked by:** 09 — Card flow; 15 — Active cards with actions; 16 — Ongoing effects

**Status:** ready-for-agent

- [x] Setup deals two Corporations to each Player; the choice is hidden until revealed, and its starting values apply.
- [x] Every Corporation has at least one scenario test covering its starting values and ability.
- [x] This ticket's entries in the card mismatch report are resolved.
- [x] The GUI shows each Player's Corporation with its ability.
- [x] The fuzzer plays with random Corporations.

Hand-off from ticket 16 (2026-10-31): many abilities fit its effect data forms. Discounts (Teractor's
Earth cards, Thorgate's power cards) are `"discount"`; Phobolog's titanium is `"cube_values"`;
Inventrix's Requirements are `"requirement_steps"`; Interplanetary Cinematics' Events, Saturn
Systems' jovian Tags, Point Luna's Earth Tags and Tharsis Republic's Cities are `"when"` Triggers.
Some need more than the forms hold today: Saturn Systems counts any Player's Tag (`tag_played` has
no `by`), Tharsis Republic only Cities on Mars, Credicor a cost of 20 or more (Standard Projects
included), Thorgate's Power Plant Standard Project and Helion's heat as MegaCredits the payment
layer. `cards::CARDS_WITH` only looks at Project Cards (`0..PROJECT_CARDS`): extend it, and the
Player's played cards, to their Corporation.

## Comments

### 2026-10-29 — note from ticket 12 (Claude)

- **Robotic Workforce** (ticket 12) copies the production box of the Player's own building
  cards. The FAQ lets it copy a Corporation's printed Production that is not part of an effect or
  action: Mining Guild (two building Tags) and its 1 steel Production. Tharsis Republic's
  Production comes from its effect, so it is not copied. `copyable_production_boxes` in
  `engine/src/card_code.rs` looks only at played Project Cards so far.

### 2026-11-05 — hand-off from ticket 20 (Claude)

- **Helion and Local Heat Trapping:** with heat as MegaCredits, the card's 1 MegaCredit must leave 5 heat to spend. `can_carry_out` checks Resources lost against what the Player holds before paying, which holds no longer once heat can pay. The open-source game overrides `canPlay` for this.
- **Viral Enhancers' plant before a card's loss:** `card_code::plants_from_viral_enhancers` is the one place that says a Trigger's gain comes before the check. A Corporation's Tags aren't set off by `Happened::CardPlayed` when its Player starts with it: check whether any Trigger should count them. The open-source game has `onNonCardTagAdded`, for Ecological Zone and Viral Enhancers among others.

### 2026-11-05 — implemented (Claude)

**Decisions made with the user:** none. The ticket's calls were to be made without a question batch, as on tickets 19 and 20, so every call below is Claude's recommended one, recorded in `docs/rules-notes.md` ("Corporations at setup", "A Corporation counts as a card in play", "A Corporation's first action", "Helion's heat as MegaCredits", "The other Corporations' abilities", "Without a Corporation: 42 MegaCredits") as chosen on the user's instruction.

**Calls made by Claude:**
- **The order at setup.** The rulebook has Players choose a Corporation and their cards at once, then reveal in player order, gain the starting values and pay. The engine asks one Player at a time, the Corporation before the cards, since it says how many they may buy. All 12 go in the shuffle, as ADR 0003 plays Corporate Era.
- **A first action may be passed instead**, and then waits for the Player's next Turn; the rulebook only says it exists, and the open-source game offers it or Pass. One that can't be carried out (only a Scenario can bring that about) isn't offered, for as long as it can't. It counts as an Action.
- **Saturn Systems starts with 1 MegaCredit Production**, on top of the printed 1 titanium Production, as "including this" makes its own Tag count at the reveal. The open-source game does the same.
- **Which Triggers count a Corporation's Tags:** the reveal sets off `Happened::CardPlayed`, but only Saturn Systems' own can match in a real Game: nothing else with a Trigger on Tags is in play then. Viral Enhancers, Olympus Conference and Mars University come later.
- **Corporation Tags count** for Requirements, Milestones, Awards, Toll Station and Victory Points per Tag. The rulebook doesn't say; the open-source game does.
- **Heat pays for everything that costs MegaCredits** with Helion: cards, actions, Standard Projects, Milestones, Awards and cards bought. Every split is an Option. For cards bought in a Research phase, the Player says how when they are done buying, and nothing is paid until every Player is done.
- **Local Heat Trapping:** the heat a card loses can't pay for it, nor be offered.
- **CrediCor's "basic cost"** is the printed one; a discount doesn't take a card below 20.
- **Mining Guild:** once per Tile however much the bonus gives, for an Ocean too.
- **Tharsis Republic:** its own City off Mars gains 3 MegaCredits and raises no Production. Immigrant City may be played at -5 MegaCredit Production with it, as in the open-source game (found by the spec review).
- **United Nations Mars Initiative:** any raise counts, and is forgotten when the Generation ends.
- **Point Luna** isn't added: it is in ticket 16's hand-off but not in the catalog or this ticket's list.
- The *Comprehensive FAQ* could not be checked (the PDF and BoardGameGeek refuse the download). The rulebook wording comes from rulespal.com's copy; the first-action and heat code from the open-source game's `Player.ts`.

**Design notes:**
- **How a Corporation is held:** once revealed, as one more bit of `Player::played`, as a `CardSet` has room for all 220 cards. `Game::tags`, every `CARDS_WITH` intersection, `usable_actions` and `copyable_production_boxes` read it with no change, which `CARDS_WITH` now covering the whole catalog allows. The view takes it out: `played_cards` stays Project Cards only, so `every_card_in_exactly_one_place` still reports a Corporation in a pile, and it shows as `corporation`. `CardResources` never sees one, as none holds any.
- **Setup:** `corporations.rs` has `ChoosingCorporation` (`Player::choosing_corporation`, dealt and picked), `Waiting::Corporation`, `reveal_corporation` and `first_action_to_take`. While choosing, nobody holds anything; `megacredits_to_buy_with` reads the starting MegaCredits from the Corporation picked, and the view gives it as `buying.megacredits`.
- **Payment layer:** `Payment` gained `heat`, and `ways_to_pay` an amount of heat. `expenses.rs` has `Expense` (`StandardProject`, `Milestone`, `Award`, `BoughtCards`, `KeptCards`), `spend_on` and `Waiting::Expense`, so all those go through one way to pay, with the option details `{"type": "payment", "paying_for", "cost", ...}`. `usable_heat` is the one place that knows Helion. `standard_project_cost` is the one that knows Thorgate's Power Plant.
- **Effect data:** all 12 have `"effects"`, starting values as `"resources"` and `"production"`. New forms: `"first_action"`, `"greenery_discount"`, `on_mars` on `tile_placed`, `tag_played_by_anyone`, `cost_at_least`, `placement_bonus`. The five actions that spent MegaCredits as a Resource loss (Search for Life, Space Mirrors, Industrial Center, Restricted Area, Underground Detonations) are now `"pay"`, so that heat can pay them. Rust: `card_code` names Helion, Thorgate, Tharsis Republic (for Immigrant City) and United Nations Mars Initiative.
- **Old Replays and Scenarios:** `Settings::corporations` reads as off from an old Replay (`#[serde(default)]`), with no extra random numbers, so it plays as it did at 42 MegaCredits. 60 random Games saved by the 12e135e engine were rebuilt by this one with the same scores, board and Players. A Scenario keeps its 42 MegaCredits default; `"corporation"` names a revealed one and gives no starting values, and `"first_action_due"` says whether its first action is still due.
- **GUI:** the buying panel offers the Corporations with the Project Cards above them, then shows the one chosen above the cards to buy and what may be spent. Player boards show the Corporation and its ability, or that it is hidden; played cards have a Corporation group, where United Nations Mars Initiative's action is clicked. `PaymentPicker` has a heat stepper, and paying for something other than a card says what.
- **Tests** (1,652 in all, up from 1,529): a file for each of the 12, each with its starting values through real setup (`helpers.start_as`) and its ability; `tests/rules/test_corporations.py`. Tests of buying that don't concern Corporations use `corporations=False`.
- **Fuzzer:** it plays random Corporations. New invariants `corporations_stay_hidden_until_they_are_revealed`, `first_action_comes_first`, `costs_of_standard_projects_and_greeneries_are_as_printed`, `ways_to_pay_cover_the_cost`, `tags_shown_count_the_corporation`, with hand-written lists. One fuzz run found a real bug: cards bought with an action vanished from the view while the Game asked how to pay for them.
- **In 300 random Games** (2–5 Players), the Corporations picked: CrediCor 91, EcoLine 87, Helion 84, Interplanetary Cinematics 81, Inventrix 92, Mining Guild 78, PhoboLog 96, Saturn Systems 91, Teractor 94, Tharsis Republic 90, Thorgate 85, United Nations Mars Initiative 81. Used: first actions 182; Triggers Tharsis Republic 1,223, CrediCor 456, Saturn Systems 281, Interplanetary Cinematics 225, Mining Guild 122; United Nations Mars Initiative's action 253; Thorgate's Power Plant 500; EcoLine's 7-plant conversion 468; heat picked in 2,096 ways to pay (card or action 453, Standard Project 834, cards bought 768, Milestone 25, Award 16).
- **Checked in the browser** (1440×900, one human and in Hotseat, a Scenario loaded through a second WebSocket): two Corporations offered with the 10 Project Cards above; what was chosen hidden from the other board and from the next Player in Hotseat; both revealed with their abilities and starting values; Helion's heat stepper paying Sponsors; Tharsis Republic's first action and its City Decision; a Corporation group among the played cards; an old Replay showing 42 MegaCredits and no Corporation line. No console errors.
- **Game length and speed** (2026-11-05, on mains, charging, "performance" profile, the variants measured one after the other):
  - Fuzzing: 20,000 Games with 2–5 Players and 13,159,474 Decisions in 356 s, on the final engine, clean, the longest Game 34 Generations. Two earlier runs were clean too (13,183,525 and 13,179,700 Decisions), before the review's fixes and the speed fixes.
  - Benchmark: 5,307 Games/s in 1 process and 53,785 on 16. A copy takes 0.21 to 0.91 µs. Every target met.
  - In identical Games (683 picks), this engine with the new data left out and `corporations=False`, in three rounds against 12e135e: 5,437 and 54,829 Games/s, against 5,643 and 56,949, so the code costs about 3.7 %. It was about 7 % at first: `spendable_megacredits` no longer works out what cubes are worth for every Milestone, `plants_per_greenery` returns early without a discount, and `spend_on` lists no ways to pay without heat.
- **Card mismatch report:** 0 differences, now including the starting MegaCredits of every Corporation, as ticket 07 asked. **Card coverage:** no card is left on it.

**Code review** (`/code-review`, standards and spec):
- Fixed:
  - Immigrant City at -5 was refused with Tharsis Republic.
  - In Hotseat a Player's hidden pick showed on their board to the next Player, and in a Game without Corporations the boards said one was hidden.
  - The mismatch report didn't compare starting MegaCredits (ticket 07's note).
  - `CorporationChoice` used the _Avoid_ word "choice": it became `ChoosingCorporation`.
  - `Game::first_action_due` shared its name with the Player's field: `first_action_to_take`. `spendable_megacredits` for the repeated `spendable(player, false, false, 0)`. `tags_on` and `named_once` for duplicated bodies. `impl Extend` removed.
  - Doc comments the change had made false (Active-only wording, "what a Player starts with", and others). The test of the Corporation not chosen now tracks it, and an old Replay's test now plays its picks. An unrelated unquoting that ruff's autofix made in `session.py` was undone.
- Left as is:
  - **One-card data forms beside code for Helion, Thorgate and United Nations Mars Initiative:** `greenery_discount`, `cost_at_least`, `placement_bonus` and `tag_played_by_anyone` are effects other cards could have and fit the Trigger language (ADR 0009); Helion's heat and Thorgate's Power Plant change the payment layer, and the action's condition is a one-off.
  - **`ways_to_pay`'s parameters, and `log_heat_paid` three times in one `match`:** a bundle or a second `match` reads no better.
  - **`Expense::BoughtCards` returns early and has an `unreachable!`:** it is the one Expense paid later, as nothing shows until every Player is done.
  - **`first_action` as `Effects` though only `draw` and `tiles` are read:** the same shape as `action`, carried out by `carry_out`.
  - **`first_action_due` stays true while the first action can't be carried out:** it is still owed if an Area frees up, and only a Scenario gets there.
  - **`waiting_on_random_bot_to_draft_or_buy`'s name** now covers choosing a Corporation and paying too; its docstring says so.
  - **`Expense`** isn't in `CONTEXT.md`: it names the engine's code, not a term of the rules.
  - **Two view fields only the fuzzer reads** (`first_action_due`, `terraform_rating_raised`): it can't see the rule otherwise, and the AI will want them.

**Open points:**
- **Hand-offs:** ticket 22 (the state editor and Corporations), ticket 24 (the coverage check can fail now, and the 100,000-Game run), ticket 25 (what to watch in play).
- **Still open from earlier tickets:** Scenarios refuse an Ocean on land and don't keep Cities apart (ticket 22); `implemented_cards_first` changes nothing (ticket 24); the paw's emoji font (ticket 23).
- **Status line:** it stays `ready-for-agent`, because `docs/agents/triage-labels.md` has no "done" label.
