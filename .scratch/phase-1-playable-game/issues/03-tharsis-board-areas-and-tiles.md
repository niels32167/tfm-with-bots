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

- [ ] Every Tharsis Area, with its reservation and placement bonus, matches the official board (checked against the rulebook and the open-source game's board).
- [ ] Ocean Tiles go only on ocean Areas, and at most 9 are placed.
- [ ] A Greenery goes next to one of its owner's Tiles when possible, otherwise on any legal Area, and never on an ocean Area.
- [ ] A City never goes on an ocean Area or next to another City.
- [ ] Steel, titanium and plant placement bonuses are granted, plus 2 MegaCredits per adjacent Ocean.
- [ ] A Greenery raises Oxygen one step (and Terraform Rating by one) while Oxygen is below its maximum; placing an Ocean raises Terraform Rating.
- [ ] The three Standard Projects and the plant conversion are offered only when the Player can afford them and a legal Area exists.
- [ ] A choose-an-Area Decision lists only legal Areas, and the GUI accepts a click on the board.
- [ ] Every rule above has a scenario test.
