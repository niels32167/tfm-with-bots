# 18 — A screen to play and learn at

**What to do:** The user's requests of 2026-11-24, after playing in the GUI:

1. The new-Game screen is too small to see every bot. A more inviting intro screen, with a drop-down for the bots.
2. Choosing cards (Corporation, Prelude Cards, Draft, ...) toggles a highlight; **Done** sends the choice.
3. At setup the Corporations, Prelude Cards and Project Cards show at the same time, a titled row each, so that combinations can be tried.
4. What was done automatically, such as the second Prelude Card and drawing cards, needs a click: "Play ...", "Draw cards".
5. Undo only where it gives no advantage: within the current Turn, and never past cards seen or another Player's actions.
6. A toggle shows what the bot would do, to learn from it.

**Status:** done

- [x] 1 intro screen · [x] 2 toggling and Done · [x] 3 setup rows · [x] 4 clicks · [x] 5 undo · [x] 6 advice

## Comments

### 2026-11-24 — implemented (Claude)

The design is in ADR 0015. Decisions made by Claude, on the user's standing instruction to choose the recommended ones:

- **End Turn button after the second Action.** Not asked for, but without it the last Action of a Turn could never be undone, as the bots act at once.
- **"Current round" is read as: until something hidden is seen.** Another Player's pick, a card drawn, looked at, dealt or passed on in the Draft, the end of a Generation, or the end of a phase chosen in secretly. Once the others have passed, one Player's Turns run on and may be undone through.
- **Hotseat keeps unlimited undo.** Everything is shown there, and fuzz failures are opened that way.
- **Sell Patents and Mars University's discard** are toggled too.
- **Advice** is suggested from the Value Bot (strongest that answers at once); Search, Imitation and Card Economy can be chosen. In 3–5 Player Games only Card Economy can, as the models' encoding is for 2 Players; the drop-downs now say so.
- **Not changed:** playing a card from the hand, Standard Projects and Tiles are still one click, since they can be undone.

**Code review:** fixed: undo after a Draft pick that passed the hands on showed the next hand (found by the spec review, now tested); the setup rows didn't fit a small laptop window; the confirmation claimed undo was off in Hotseat too; glossary words; duplicated test helpers and zoom hooks. Left as is: kinds of choices are listed in both the server and the GUI; End Turn is asked for also when nothing can be undone, so that it is always the same.

**Open points for the user:** Hotseat's unlimited undo, and the meaning of "current round" above. The hosted image is not rebuilt.

**Checks:** 2,311 tests, clippy, `cargo fmt`, the GUI build, and the browser at 1440x900, 1366x650, 1000x560 and 700x700. A whole Game against a bot was not played to its end in the new GUI.
