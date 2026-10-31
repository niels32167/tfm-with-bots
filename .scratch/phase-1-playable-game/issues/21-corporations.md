# 21 — Corporations

**What to build:** At setup each Player is dealt two Corporations, picks one, and starts with its starting MegaCredits and other Resources and Production. This replaces the temporary fixed amount used so far. The choice is taken one Player at a time and stays hidden until it is revealed as the rules say.

All 12 Corporations work as printed:
- Credicor, Ecoline, Helion, Interplanetary Cinematics, Inventrix, Mining Guild, Phobolog, Tharsis Republic, Thorgate and United Nations Mars Initiative;
- the Corporate Era Saturn Systems and Teractor.

Their abilities reuse the action, trigger, discount and payment machinery. For example, Helion lets heat pay as MegaCredits.

The Beginner Corporation is left out: it isn't on the card list, and it belongs to the beginner variant, not the Corporate Era game.

**Blocked by:** 09 — Card flow; 15 — Active cards with actions; 16 — Ongoing effects

**Status:** ready-for-agent

- [ ] Setup deals two Corporations to each Player; the choice is hidden until revealed, and its starting values apply.
- [ ] Every Corporation has at least one scenario test covering its starting values and ability.
- [ ] This ticket's entries in the card mismatch report are resolved.
- [ ] The GUI shows each Player's Corporation with its ability.
- [ ] The fuzzer plays with random Corporations.

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
