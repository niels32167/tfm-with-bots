# 22 — Dev panel

**What to build:** A panel for hunting rule bugs, toggled on and off over the game view. It has:
- the seed;
- the full game log;
- Replay step-through, forwards and backwards;
- a full-view switch showing all hands and the deck order;
- a state editor.

With the state editor, the user can give a Player Resources or Production, set Global Parameters, put specific cards in a hand or among played cards, place a Tile, and set the Generation. An edited state is a Scenario, saved and loaded like any Replay, so a setup found in the GUI can become an automated test.

**Blocked by:** 02 — New Game setup, seed, undo and Replays; 08 — Playing Project Cards

**Status:** ready-for-agent

- [ ] The panel can be toggled without disturbing the Game.
- [ ] Replay step-through moves forwards and backwards and shows the state at each step.
- [ ] The full-view switch shows all hands and the deck order.
- [ ] Each kind of state edit above works and produces a Scenario that can be saved and reloaded.
- [ ] A saved Scenario can be used directly in a scenario test.

## Comments

### 2026-10-29 — notes from tickets 11 and 12 (Claude)

- **Scenarios refuse** a Greenery on an Area reserved for Oceans and an Ocean on land, so they
  can't yet describe a position after Mangrove (ticket 11) or Artificial Lake (ticket 12). The
  state editor will need them: allow one per card played that puts one there (Oceans belong to
  nobody, so one Ocean on land per Artificial Lake played by anyone).
- **Scenarios don't check** that Cities keep apart, so they accept a position after Urbanized Area
  (ticket 12), but also Cities next to each other that no rule allows. The fuzzer's
  `tiles_only_on_legal_areas` says what is legal, and the state editor could reuse its rules.

### 2026-11-01 — notes from ticket 18 (Claude)

- **Scenarios now describe special Tiles and Land Claim**: `{"area": "C4", "tile": "special",
  "card": "nuclear_zone", "owner": 0}` (Capital's is a `"city"` with `"card": "capital"`), a City on
  an Area reserved for a card's City, Mohole Area's Tile on an Area reserved for Oceans, and
  `"land_claim": {"area": "C3", "player": 1}`. They don't check that the Tile's card was played, or
  where a special Tile's card allows it (Lava Flows on a volcano, and so on); the fuzzer's
  `special_tiles_where_their_cards_put_them` and `each_reserved_area_used_only_by_its_card` say
  what is legal, and the state editor could reuse them.

### 2026-11-04 — hand-off from ticket 19 (Claude)

Scenarios now take a Player's `"card_resources"`, such as `{"tardigrades": 3}`: the state editor should let the user set them on played cards that hold some (`effects.holds` in the catalog). The Scenario refuses them on a card not played or holding none.
