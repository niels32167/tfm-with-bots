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

- [ ] The Production phase follows the order above, and the Production limits are enforced.
- [ ] Power Plant and heat conversion are offered only when legal.
- [ ] Each track bonus goes to the Player who raised the parameter, including chains such as 8 % Oxygen giving a Temperature step that hits a bonus.
- [ ] Raising a maxed parameter gives no step and no Terraform Rating.
- [ ] The Game ends after the Generation in which all three are maxed.
- [ ] The final Greenery conversion happens in player order.
- [ ] The GUI shows player boards and all three tracks.
- [ ] Every rule above has a scenario test.
