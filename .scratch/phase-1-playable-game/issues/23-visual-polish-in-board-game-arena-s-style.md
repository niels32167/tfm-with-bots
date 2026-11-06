# 23 — Visual polish in Board Game Arena's style

**What to build:** Bring the GUI as close as possible to Board Game Arena's Terraforming Mars (ADR 0006).

Start by studying its game view in the browser pane. If a page needs a login, the user logs in themselves; never enter credentials. The user's screenshot of the Asmodee digital game is a second reference for the tracks.

Polish:
- the board on a public-domain NASA Mars image (downloaded with the user's OK first);
- the Oxygen arc, the thermometer with its bonus markers, and the Ocean counter;
- the Standard Projects panel, and the Milestones and Awards bar;
- player boards;
- the hand, and played cards grouped by type with Card Resources;
- card zoom;
- a status bar in Board Game Arena's style, and the payment picker;
- the pacing of Random Bot moves.

**Blocked by:** 05 — Milestones, Awards and final scoring; 08 — Playing Project Cards

**Status:** ready-for-agent

- [x] Notes on Board Game Arena's layout (regions, what each shows) are recorded under Comments in this ticket before building.
- [x] Every element in the list above is restyled, and side-by-side screenshots against Board Game Arena are attached under Comments.
- [x] The layout works on desktop browser widths from 1366 to 2560 pixels without horizontal scrolling.
- [x] Nothing in the dev panel or in gameplay breaks; the WebSocket smoke test and the scenario tests still pass.

## Comments

### 2026-11-05 — hand-off from ticket 20 (Claude)

Ecological Zone's Tile uses the card's paw (U+1F43E) in `SPECIAL_SYMBOLS`. Unlike the other symbols, the browser draws it from a colour emoji font: blue here, ignoring `.special-symbol`'s fill, and small on the tile. It is legible but differs by system; a drawn SVG paw would match the other Tiles.

### 2026-11-06 — notes on Board Game Arena's layout (Claude)

Studied before building, in the browser pane, without a login: the "Example game" Replay linked from its Terraforming Mars page (table 873680897, moves 1 to 133, 1440×900). Optional cookies declined. Its game view is an iframe (`archive/frame.html`), reachable from the page's JavaScript. The second reference is the user's image of the Asmodee digital game's board, sent in the conversation of 2026-11-06; as the spec says, it is not in the repo.

**The page, top to bottom, and two columns under the top bar:**
- **Top bar** (white, about 50 px): logo, table and move number, progress.
- **Left column** (1178 of 1440 px), scrolling: status bar, hand, own Player's area, the board, the other Players' areas, then the three "all cards" bars.
- **Right column** (240 px): the settings box, one board per Player, then the game log, which scrolls with the page. A preference moves the log to a second column.
- **Background:** a black starfield behind everything; panels are translucent grey over it.

**Status bar** (`#page-title`, background #f4f4f4, 17.6 px bold Roboto, sticky):
- One centred sentence, with the Player's name in their colour: "You must select a location to place a Greenery tile, adjacent if possible [Greenery]".
- Options as buttons on the same line, wrapping below: pale blue (`rgba(33,150,243,.78)`, 6 px radius, 14 px bold), brown for "Show on Map", and **red for Undo** at the far right.
- While another Player acts, a second line gives the latest log entry: "ae chaim is playing their turn" over "ae chaim places Natural Preserve on Tharsis Hex 5,8".
- A payment shows "You must pay 18 M€ (can use Steel) [Aquifer Pumping]", with one button per way to pay (6 steel, 18 M€) and a Custom button.

**Hand:** a translucent grey panel with "Hand" written up its left side; the cards in wrapping rows, each with its full picture.

**Own Player's area** (grey panel outlined in their colour, all the left column's width):
- A tab with their name, the Corporation's logo beneath it.
- A strip: Terraform Rating, then each Resource as icon over count over Production.
- A row of round Tag counters.
- A red box with the number of Events and a list icon: they are folded away.
- **Four columns with coloured headers,** each with a count and a view mode: Headquarters (grey, "Grid"), Automated (green, "Stack"), Effects (light blue, "Stack"), Actions (blue, "Stack"). In a stack only each card's top shows, and the last one shows whole.

**Board** (`#main_board`, 810×631 at this width), one picture on the starfield:
- **Mars:** a pale NASA-style globe, about 73 % of the height. Thin white hexagons with no fill, reaching past the globe in the widest rows. Reserved Ocean Areas are tinted blue. Bonuses are small green and black squares. Place names (Lunae Planum, Sinai Planum, Solis Planum) are printed faintly on the globe.
- **Tiles:** an Ocean is a blue hexagon with a wave symbol, a Greenery green with a Player's cube on it, a City grey with a skyline.
- **Oxygen arc:** a thick silver band over the top of the globe, 0 to 14 in gold numerals, the current one ringed; 14 is gold. A small thermometer sits by 8 %.
- **Thermometer:** a tall tube at the right from the globe's top to its bottom, blue at the bottom through purple to red, +8 to −30, the current step in a white box, and a round blue bulb reading the Temperature. Bonuses sit on its left: a heat square at −24 and −20, an Ocean hexagon at 0.
- **Ocean counter:** a blue hexagon at the top right holding **how many are left**: 9 at the start.
- **Above the thermometer:** the Generation in a ringed circle and a Score button. Top left: Draw and Discard counts.
- **Off Mars:** Phobos Space Haven as a grey asteroid and Ganymede Colony as a purple hexagon, both left of the globe, upper part.
- **Standard Projects:** a pale panel at the lower left, title on top, six rows: gold price, arrow, what it gives, name on a yellow label.
- **Milestones and Awards:** two silver panels side by side along the bottom, each with a gold title plate, three price tokens (8 8 8, and 8 14 20), a coloured tag for the costs' owners, and five entries: an icon, a name and each Player's standing.
- The Asmodee board adds a Terraform Rating track round the whole edge (1 to 100); Board Game Arena leaves it out.

**Player board** (right column, background #9e9e9e, black text, rounded on the left only):
- Name in their colour, Terraform Rating, Hand size, a red "1" token for the first player, the Corporation's logo.
- Six cells in one row, each with the Resource's colour: icon and count on top, the Production on a brown square underneath.

**Settings box:** zoom, help and settings buttons over four readings: Oxygen, Temperature, Oceans and Generation. It stays in view when the board has scrolled away.

**Game log:** white rows with a black rule between them, 13.6 px; Players' names bold in their colour, card names underlined, small Resource icons in the sentences, a clock time between groups.

**Card zoom:** hovering shows a cream tooltip beside the card, not over it: the card large, and beside it its type and number, cost, Tags, Requirement and rules text. A hovered Area shows its name and coordinates the same way.

**Pacing:** each change is animated and named on the status bar's second line.

### 2026-11-06 — implemented (Claude)

**Decisions made with the user:**
- **The NASA image:** the user approved `Mars_Valles_Marineris.jpeg` (1552×1552, 256 KB; a Viking 1 Orbiter mosaic by NASA/USGS, JPL PIA04304, public domain) from upload.wikimedia.org. It is `gui/public/mars/mars-valles-marineris.jpeg`, credited in the README.
- **The Asmodee reference:** the user sent their image of the board in the conversation, so it stays out of the repo, as the spec says. It guided the Oxygen arc, the thermometer, the Ocean hexagon, the Standard Projects panel and the two silver bars.

No login to Board Game Arena was needed: its Example game Replay opens for a visitor.

**The side-by-sides** are six images in `.cache/ticket-23/side-by-side/`: the board, the Player's area with the card zoom, the Player's area with the boards, the status bar and payment, buying, and the hand. This tracker is plain markdown with no attachments, and they hold Board Game Arena's art, so they are kept on this machine and out of git (`.cache/` is ignored), rather than attached. Chosen by Claude (2026-11-06), on the user's instruction to make the calls.

**Calls made by Claude** (each chosen 2026-11-06, on the user's instruction to choose the recommended decisions):
- **The board is one SVG**, as on both references, so the tracks, Standard Projects, Milestones and Awards scale with Mars. The parts stay in their own files.
- **The hand stays docked at the bottom,** and the board comes first under the status bar with the Players' areas beneath it. Board Game Arena has the hand and own area above the board, which puts the board below the fold at 1440×900. The dock was decided with the user on ticket 09, so this stands against the "as close as possible" of this ticket.
- **No Terraform Rating track round the edge:** the Asmodee board has one, Board Game Arena does not, and it is the primary reference.
- **The Ocean counter holds how many are left** and the readings box how many are placed, both as on Board Game Arena (it showed 5 and 4 together). The tooltip says which.
- **Not copied:** the Grid/Stack switches on columns, zoom and 3D buttons, the Score button, "Show on Map" and Area buttons in the status bar. Areas are lit on the board, which is in view. Final scores stay as they were.
- **The payment picker stays steppers,** as the spec asks, with icons in place of words. Board Game Arena has one button per way to pay, plus Custom.
- **Blue cards split into Effects and Actions** by whether the card has an action. The Events fold away per Player, as there.
- **Undo moved to the status bar,** in red, and to the looking-back bar. The Generation moved to the board and the readings.
- **Bonuses and Standard Projects use the card list's icons;** Tiles and cubes are drawn. Only the paw was asked for among special Tiles' symbols, so the rest are still characters from a font.
- **Random Bot pacing:** no pause for a Decision with one Option, as there is nothing to watch, while choosing a Corporation, drafting and buying still take no pause at all. The status bar's second line says what it last did, and a Tile arrives with a short bounce. A one-Option Decision reveals nothing hidden: a card it could play comes with a Pass, and a card in hand with Sell Patents, and hand size is public.
- **The card gallery keeps its own hover and click:** it is for browsing, and isn't on the ticket's list. Every card elsewhere uses the new zoom.

**Design notes:**
- **GUI:** `MarsBoard` draws the board from `shown`, with `OxygenTrack`, `TemperatureTrack`, `OceanTrack`, `StandardProjects`, `MilestonesAwards` and `boardLayout.tsx`. New: `GlobalReadings`; `CardZoom`, which enlarges anything with `data-zoom-card`, so a new place only marks its card. The paw is the SVG `Paw`, ending the hand-off above.
- **Server:** `GameSession.random_bot_pauses_before_picking`. **The engine is unchanged,** so the fuzz, benchmark and mismatch report weren't run; those at ticket 22 still hold.
- **Tests** (1,711 in all, up from 1,708): `tests/server/test_random_bot_pacing.py`, written first: no pause with one Option, a pause with several, none for drafting or buying. The WebSocket smoke test and the scenario tests pass, and `npm run build` is clean.
- **Checked in the browser:**
  - **Widths:** 1366×768, 1440×900 and 2560×1440: no horizontal scrolling, with the dev panel open and closed, and no element past the window's edge. At 1366×768 the whole board fits above the dock, 609 px wide, in a Game of 2 and of 5.
  - **Screens:** one human from setup through Corporation, buying and Action; Hotseat with its tabs and the Draft; final scores; every Global Parameter at its maximum.
  - **Picking:** a Standard Project, then an Area; claiming a Milestone, with the used price crossed out; a played card's action; steppers and Pay on Capital; a Random Bot's Turn, timed at about 0.75 s per pick, with its lines in the status bar. No console errors, but for those from hot reloads while editing and one server restart.
  - **Dev panel:** First and Latest show the board, tracks and readings at each step, with nothing pickable; full view; the state editor giving 99 MegaCredits, started from; Undo while looking back.

**Code review** (`/code-review`, standards and spec):
- Fixed:
  - Undo was gone while looking back.
  - The visible "maximum" on the tracks was lost: the readings say MAX now.
  - The track file's header no longer said what it held.
  - The Oxygen icon's point computed twice.
  - A magic comparison with yellow, in favour of text that reads on every colour.
  - `type` for a column, `turn` for an angle, and a shaky test helper's name.
  - Found in the browser: the buying panel's cards ran past the board over the area under it, and the Milestones bar sat under the dock at 1366×768.
- Left as is:
  - **Printed prices in `tracks.ts` and `StandardProjects`, with `view.milestone_cost` and `view.award_cost` now unused:** a board prints all three, used ones crossed out. Nothing in this Game changes them, and a discount on a Standard Project shows from its Option.
  - **`StatusSentence` matching the Player's name at the start of the sentence:** the alternative is reworking every `statusText` branch. If they differ, the name just isn't coloured.
  - **`PlayedColumn` and `PlayedCard` sharing props, tile-type branches in `TileMark`, `CorporationLine` beside `CorporationName`:** each reads no better bundled in so small a file.
  - **`MarsBoard` holding the board's gradients and `GenerationMark`:** they belong to it.
  - **`aria-hidden` on the zoom:** each card already has its name as a label.

**Open points:**
- **Hand-offs:** ticket 25 (how the board reads at 1366×768, its smallest size).
- **Still open from earlier tickets:** the 100,000-Game run and `implemented_cards_first` (ticket 24).
- **Status line:** it stays `ready-for-agent`, because `docs/agents/triage-labels.md` has no "done" label.
