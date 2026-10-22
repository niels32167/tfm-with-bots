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

- [ ] Notes on Board Game Arena's layout (regions, what each shows) are recorded under Comments in this ticket before building.
- [ ] Every element in the list above is restyled, and side-by-side screenshots against Board Game Arena are attached under Comments.
- [ ] The layout works on desktop browser widths from 1366 to 2560 pixels without horizontal scrolling.
- [ ] Nothing in the dev panel or in gameplay breaks; the WebSocket smoke test and the scenario tests still pass.
