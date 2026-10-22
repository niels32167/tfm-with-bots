# 03 — Tharsis board: Areas and Tiles

**What to build:** The Tharsis board with every Area, including the Areas reserved for Oceans, the named reserved Areas (Noctis City, plus the off-Mars Phobos Space Haven and Ganymede Colony, which stay unused until ticket 18), and all placement bonuses.

This ticket covers:
- placement of Ocean, Greenery and City Tiles;
- the Aquifer (18), Greenery (23) and City (25, plus one MegaCredit Production) Standard Projects;
- converting 8 plants into a Greenery;
- Greeneries raising Oxygen, and Oceans counting towards 9;
- 2 MegaCredits for each Ocean next to a placed Tile.

Steel, titanium and plants become Resources Players can hold; their Production comes in ticket 04. Placement bonuses that draw cards start working once there is a deck (ticket 08).

The GUI draws the board as clickable Areas (simple styling for now, polished in ticket 23), shows Tiles in their owner's colour, and highlights the legal Areas whenever a Decision asks for one.

**Blocked by:** 01 — Walking skeleton

**Status:** ready-for-agent

- [x] Every Tharsis Area, with its reservation and placement bonus, matches the official board (checked against the rulebook and the open-source game's board).
- [x] Ocean Tiles go only on ocean Areas, and at most 9 are placed.
- [x] A Greenery goes next to one of its owner's Tiles when possible, otherwise on any legal Area, and never on an ocean Area.
- [x] A City never goes on an ocean Area or next to another City.
- [x] Steel, titanium and plant placement bonuses are granted, plus 2 MegaCredits per adjacent Ocean.
- [x] A Greenery raises Oxygen one step (and Terraform Rating by one) while Oxygen is below its maximum; placing an Ocean raises Terraform Rating.
- [x] The three Standard Projects and the plant conversion are offered only when the Player can afford them and a legal Area exists. Once 9 Oceans are placed, Aquifer is still offered and does nothing, as Asteroid does at maximum Temperature (see docs/rules-notes.md).
- [x] A choose-an-Area Decision lists only legal Areas, and the GUI accepts a click on the board.
- [x] Every rule above has a scenario test.

## Comments

### 2026-10-22 — implemented (Claude)

**Decisions made with the user:**
- **Test seams:** the Python engine module only. Rules are tested in `tests/rules/` (board, Oceans, Greeneries, Cities, placement bonuses, Standard Projects) and Replays in `tests/engine/`. The server passes Area Decisions through unchanged, so it got no new tests. The board GUI was checked by hand in the browser.
- **Area names:** Areas are named A1–J5, as the open-source game labels Tharsis: rows A to J from the top (there is no row I), numbered from the left. Noctis City is E3. The Areas off Mars go by name: `phobos_space_haven` and `ganymede_colony`.
- **Oceans in a Scenario:** a Scenario lists its Tiles (`{"area", "tile", "owner"}`), and the number of Oceans is the number of Ocean Tiles. Oxygen has its own field.
- **Card bonuses:** until there is a deck (ticket 08), a card placement bonus gives nothing. The game log says what it would give.
- **Aquifer at 9 Oceans** follows the Asteroid call: it is still offered, costs 18 MegaCredits and does nothing else. The open-source game agrees. The criterion above is reworded to match, and `docs/rules-notes.md` has the details.

**Design notes:**
- **Engine:**
  - `engine/src/board.rs` holds the printed board, one Area per row of the table: reservation, placement bonus and printed name. It also works out adjacency, with each row centred under the widest one, and keeps the Tiles placed as a fixed-size array, so copying a Game stays a plain value copy (ADR 0004).
  - Legal Areas are worked out in one place. `areas_for` lists them, and `has_area_for` stops at the first one when deciding whether an Action is offered.
- **Decisions:** a Standard Project or plant conversion that places a Tile is paid for first. It then waits on a choose-an-Area Decision (kind `"area"`) whose Options have details `{"type": "area", "area": "C3", "tile": "city"}` and labels like "Place the City on B2 (Tharsis Tholus)". Undo goes back to that Decision, like any other.
- **View:** the Player View (and full view) gains `oxygen`, `oceans` and `board`. The board is every Area with `area`, `name`, `row`, `position`, `reserved`, `bonus` and `tile` (`{"type", "owner"}` or null). Player boards gain steel, titanium and plants.
- **Names on the board:** besides Noctis City and the two Areas off Mars, the four volcanoes printed on Tharsis are named: Tharsis Tholus (B2), Ascraeus Mons (C1), Pavonis Mons (D1) and Arsia Mons (E1). Ticket 18's Lava Flows needs them. The open-source game marks those four Areas as volcanic without naming them, so the names come from the board and Mars's geography.
- **GUI:**
  - `gui/src/components/MarsBoard.tsx` draws the board as SVG hexagons over a gradient globe, which ticket 23 replaces with the NASA image.
  - Tiles are coloured by type (blue Ocean, olive Greenery, grey City) with a marker in the owner's colour.
  - During a choose-an-Area Decision the legal Areas are outlined and clickable (also by keyboard), and the rest dim. The status bar then says what to place, without one button per Area.
  - A plain "Oxygen n % · Oceans n of 9" line sits above the board until ticket 04 draws the tracks.
  - With four or five Players the board area is now top-aligned, so Mars stays in view.

**Code review** (`/code-review`, standards and spec):
- Fixed:
  - the GUI called Options "choices", a glossary _Avoid_ word;
  - the test list of land Areas came from the engine's own view; it is now built from the printed board;
  - `has_room_for` became `can_take_action_placing`, and it no longer builds whole lists of Areas;
  - plainer adjacency code;
  - `OceanPlaced` became `OceansRaised`, matching `OxygenRaised`;
  - Tile names live only on `TileKind`, and `BonusItem::ALL` replaces a hand-typed list;
  - tooltips use the Player names from the view;
  - two missing tests: converting plants at maximum Oxygen, and placing the 9th Ocean in play.
- Left as is:
  - **No Area buttons in the status bar.** Spec story 66 mentions Options as buttons, but with up to 48 Areas the highlighted board is the better control, and Board Game Arena does the same.
  - **The board's layout maths appears twice**, once in Rust for adjacency and once in TypeScript for drawing, as do the Tile names and the Oxygen and Ocean maximums.
  - **Steel, titanium and plants as separate fields** in `Player`, `ScenarioPlayer` and the views. Ticket 04 adds energy, heat and all six Productions, which is a good moment for a `Resources` struct.
  - **The volcano names and the Oxygen/Oceans line** are small additions beyond the ticket text (see Design notes).

**Open points:**
- **Ticket 18:** a Scenario still refuses Tiles on Noctis City and the two Areas off Mars ("reserved for the … card"). Once those cards exist, it must accept their own Tiles there, or a position after Noctis City is played can't be set up.
- **Ticket 04:** the Game still ends on Temperature alone. Track bonuses, Oxygen and Ocean tracks, and the end on all three Global Parameters are ticket 04's.
- **Ticket 06:** legal Areas are worked out afresh for every Decision. Adjacency is computed on the fly, so the benchmark will show whether a precomputed neighbour table is worth it.
- **Tile colours:** the ticket says Tiles are shown "in their owner's colour". Here the owner shows as a coloured marker on a Tile coloured by type, as on the physical board. Say if you'd rather have whole Tiles in the owner's colour.
