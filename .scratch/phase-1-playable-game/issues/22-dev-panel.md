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
