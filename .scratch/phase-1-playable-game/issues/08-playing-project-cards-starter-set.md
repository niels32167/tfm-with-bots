# 08 — Playing Project Cards (starter set)

**What to build:** The machinery every card batch builds on, proven with a starter set of 11 simple Automated cards:
- #022 Black Polar Dust
- #045 Nuclear Power
- #053 Lake Marineris
- #056 Mine
- #060 Trees
- #087 Grass
- #113 Solar Power
- #138 Strip Mine
- #141 Power Plant
- #144 Titanium Mine
- #168 Windmills

This ticket covers:
- **Playing a card.** "Play a Project Card" becomes an Action, offered only when the Player meets the card's Requirements and can pay.
- **Payment Decision.** One Option per distinct legal split between MegaCredits, steel (2 each, for cards with a building Tag) and titanium (3 each, for cards with a space Tag). The GUI shows these as a payment picker.
- **Effect data (ADR 0009).** Primitives: gain or lose Resources, change Production, place a Tile, raise a Global Parameter, draw cards, gain Terraform Rating.
- **Central rules.** Requirement checks (Global Parameter minimums and maximums, Tag counts, Production) and Tag counting live in one central place.
- **Scoring.** Victory Points printed on cards count in final scoring.
- **Deck.** There is now a deck: placement bonuses that draw cards take effect. Until ticket 09, a new Game simply deals each Player a few cards so the starter set can be played in the GUI.
- **GUI.** It shows the hand and each Player's played cards, grouped by type.

**Blocked by:** 04 — Resources, Production and the end of the Game; 07 — Card import and card gallery

**Status:** ready-for-agent

- [ ] A card is offered only when it is legal to play: its Requirements are met and it is affordable with the allowed Resources.
- [ ] Payment Options cover every legal split, and the GUI payment picker uses them.
- [ ] Each starter-set card has a scenario test covering its Requirements, its effect and its Victory Points.
- [ ] Scenarios can put specific cards in a Player's hand and among their played cards.
- [ ] Scenario tests now cover Builder, Planner and Scientist (ticket 05).
- [ ] A coverage check lists every catalog card without a scenario test. It only reports for now; ticket 24 makes it fail on gaps.
- [ ] Card-draw placement bonuses work.
- [ ] Final scoring includes card Victory Points.
