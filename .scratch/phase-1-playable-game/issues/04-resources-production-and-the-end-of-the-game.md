# 04 — Resources, Production and the end of the Game

**What to build:** This ticket covers:
- **Resources and Production.** All six Resources (MegaCredits, steel, titanium, plants, energy, heat) and their Production. MegaCredit Production can go down to −5; all other Production stays at 0 or above.
- **Production phase.** Energy turns into heat, then every Resource gains its Production, and MegaCredits also gain Terraform Rating.
- **Power Plant.** The Standard Project costs 11 and gives one energy Production.
- **Heat conversion.** 8 heat converts into a Temperature step.
- **Track bonuses.** Heat Production at −24 °C and −20 °C, an Ocean at 0 °C, and a Temperature step at 8 % Oxygen.
- **Maximums.** Temperature +8 °C, Oxygen 14 %, 9 Oceans.
- **End of the Game.** It ends after the Generation in which all three Global Parameters are maxed, replacing the Temperature-only end from ticket 01. After that final Production phase, Players may convert plants into Greeneries in player order.

In the GUI, each Player gets a board showing Resources, Production and Terraform Rating, and the Oxygen and Ocean tracks appear next to Temperature.

**Blocked by:** 03 — Tharsis board

**Status:** ready-for-agent

- [x] The Production phase follows the order above, and the Production limits are enforced.
- [x] Power Plant and heat conversion are offered only when legal.
- [x] Each track bonus goes to the Player who raised the parameter, including chains such as 8 % Oxygen giving a Temperature step that hits a bonus.
- [x] Raising a maxed parameter gives no step and no Terraform Rating.
- [x] The Game ends after the Generation in which all three are maxed.
- [x] The final Greenery conversion happens in player order.
- [x] The GUI shows player boards and all three tracks.
- [x] Every rule above has a scenario test.

## Comments

### 2026-10-23 — implemented (Claude)

**Decisions made with the user:**
- **Test seam:** the Python engine module only. Rules are tested in `tests/rules/` (Production, Standard Projects, heat conversion, track bonuses, end of the Game, final Greenery conversion). The server passes the new Decisions through unchanged, so it got no new tests; its undo test now starts from a Scenario one Asteroid short of a terraformed Mars, because a Game no longer ends on Temperature alone. The GUI was checked by hand in the browser.
- **Resources:** one `Resources` struct (`engine/src/resources.rs`) holds all six, used for what a Player holds and for their Production. Scenario players and player boards both read `{"resources": {...}, "production": {...}, "terraform_rating": n}`. A Scenario may name only some Resources; the rest keep their defaults (42 MegaCredits, nothing else). The `player()` test helper still takes `player(megacredits=20, plants=8, production={"heat": 2})`, and `resources(game, i)` and `production(game, i)` read them back.
- **Final Greenery conversion:** a Decision of kind `"final_greenery"` with Options "Convert 8 plants into a Greenery" and "Done", followed by the usual `"area"` Decision. Order follows the open-source game: player order from the final Generation's first player, each Player finishing before the next. A Player without 8 plants or a free Area is passed over.
- **Heat conversion at +8 °C** is offered and only spends 8 heat, the same call as Asteroid (`docs/rules-notes.md`).
- **The 0 °C Ocean with 9 Oceans placed** gives nothing, the same call as Aquifer.
- **The 0 °C Ocean comes before the Greenery's bonus.** The user ruled that the Player chooses the order. Ocean first is never worse for them, so the engine always places the Ocean first, then pays the Greenery's placement bonus (counting the new Ocean if it is adjacent), and asks nothing. The open-source game uses the other order. Details are in `docs/rules-notes.md`.
- **GUI tracks:** an Oxygen arc over Mars with the 8 % bonus marked, a 9-slot Ocean counter on the right, and thermometer markers at −24 and −20 °C (heat Production) and 0 °C (Ocean).

**Design notes:**
- **Engine:**
  - `Player` has `resources` and `production`, each a `Resources` indexed by `Resource`.
  - MegaCredit Production may go down to −5 (`MIN_MEGACREDIT_PRODUCTION`) and every other Production to 0 (`Resource::min_production`). A Scenario refuses Production below those limits and any negative Resource.
  - **Production phase:** energy turns into heat, every Resource gains its Production, and MegaCredits also gain Terraform Rating. The game log has one line per Player for this, e.g. "Player 1 gains 20 MegaCredits (Terraform Rating 20 + MegaCredit Production 0), 2 steel, 1 plant and 3 heat.", after a line for energy turning into heat.
  - The Standard Projects are offered in the order printed on the board, starting with Power Plant (11). Option details name it `"power_plant"`.
  - **Track bonuses** sit in `raise_temperature` and `raise_oxygen`, one step at a time, so chains (8 % → a heat Production step or 0 °C) follow on their own. Each goes to the Player who raised the parameter.
  - **Pending placements:** every Option that resolves an Action ends with `finish_unless_placing()`. The Action (or the final conversion) carries on only once no Tile is left to place, so the 0 °C Ocean can interrupt an Asteroid, a heat conversion or a Greenery. `waiting_bonus` holds a Greenery's placement bonus until that Ocean is down.
  - **End of the Game:** after the Production phase in which all three parameters are maxed, the log says "Mars is terraformed…" and the final Greenery conversion starts (`Phase::FinalGreenery`, view phase `"final_greenery"`). The first-player marker does not move on. The `Done` Option is generic, for the later "pick several, then done" chains (buying and selling cards).
- **GUI:**
  - `gui/src/tracks.ts` holds the printed track facts (limits, bonus steps), replacing the hard-coded maximums in `App.tsx`.
  - `OxygenTrack.tsx` draws the arc inside the board's SVG, with the title and reading in the top-left corner. The two Areas off Mars moved to the bottom corners to make room.
  - `OceanTrack.tsx` mirrors the thermometer on the other side of Mars.
  - Player boards show all six Resources, each with its Production, and Terraform Rating ("TR", with a tooltip) in the header.
  - The status bar has text for the final conversion; its Options are ordinary buttons. During the final conversion the current Player's badge reads "Final Greeneries", and "Passed" badges show only in the Action phase.

**Code review** (`/code-review`, standards and spec):
- Fixed:
  - the `Income` log event, which also reported steel, plants and heat, is now `Produced` (the glossary keeps "income" for MegaCredits);
  - `end_the_generation` now has a `MAX_PICKS` bound;
  - a generic `Resources::deserialize_over` became one plain function in `scenario.rs`;
  - `carry_on` became `finish_unless_placing`, and `place_in_player_order` became `index_in_player_order`, since "place" already means placing Tiles;
  - placement bonuses map onto Resources (`BonusItem::resource`), which removed repeated match arms and a second pluraliser;
  - player board tooltips name Production as the game log does ("steel Production");
  - tests that counted back from the end of the log now find their lines by content;
  - the end-of-Game parameters are named Scenarios instead of merged dicts.
  - The spec review raised the 0 °C Ocean ordering as a call I had made alone. The user then ruled on it (see above), and it was reworked.
- Left as is:
  - `match (self.placing, self.phase)` appears in both `decision()` and `finish_unless_placing()`. They answer different questions: which Decision, and what happens after a pick.
  - `production_phase` works on each Player's `resources` and `production` directly (possible Feature Envy). It is short, and a `Player::produce` would need to hand the energy amount back for the log.
  - `gui/src/tracks.ts` now copies the bonus steps as well as the limits. They are printed on the board, so the duplication with Rust was accepted, as before.
  - The six Resource names appear in Rust, the GUI's types and the test helpers. The tests keep their own copy because they go through `tm_engine` only.

**Open points:**
- **Production limits** are enforced only on Scenarios for now, since nothing lowers Production yet. Card tickets (08 onwards) must refuse effects that would push Production below its limit.
- **Negative MegaCredits:** a Scenario with Terraform Rating below 5 and MegaCredit Production −5 ends a Production phase with negative MegaCredits. Normal setup can't reach that, because Terraform Rating starts at 20 and no base card lowers your own. Ticket 06's "no negative Resources" invariant should keep it in mind.
- **Ticket 06:**
  - Log events grew from 24 to 40 bytes, because `Produced` carries a `Resources`. The copy-time benchmark should check the log against ADR 0004.
  - Random play never reaches the final Greenery conversion yet, because nothing gives plant Production before cards exist.
- **Tickets 11 and 18:** Mohole Area and Mangrove put non-Ocean Tiles on Ocean Areas. The 0 °C bonus (`place_ocean`) then needs to check that a free Ocean Area exists, not just that fewer than 9 Oceans are placed.
- **Ticket 23:** with five Players the player boards no longer fit beside Mars and the side panel scrolls.

