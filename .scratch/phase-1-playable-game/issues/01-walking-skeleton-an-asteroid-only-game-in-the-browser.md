# 01 — Walking skeleton: an Asteroid-only Game in the browser

**What to build:** The thinnest complete path through every layer, so that every later ticket only adds rules and screens.

Two Players play a Game where the only Actions are the Asteroid Standard Project (14 MegaCredits: raise Temperature one step, gain one Terraform Rating) and Passing. Each Generation has an Action phase, where Players take Turns of one or two Actions or Pass, and a Production phase that pays MegaCredits equal to Terraform Rating plus MegaCredit Production. The Game ends after the Generation in which Temperature reaches its maximum. Until Corporations exist, Players start with a fixed temporary amount of MegaCredits and Terraform Rating 20, and the final score is just Terraform Rating.

In the browser, a human plays against a Random Bot. The GUI shows Temperature, each Player's MegaCredits and Terraform Rating, the game log, and a status bar listing the current Decision's Options as buttons.

This ticket also sets up the project:
- the Rust engine built around Decisions and Options (ADR 0002);
- the Python engine module (ADR 0007);
- the local Python server with a WebSocket (ADR 0008);
- the React and TypeScript GUI (ADR 0006);
- the testing pattern every later ticket copies.

Installing the Rust toolchain (rustup) and the Python and npm packages needs the user's OK first. Python 3.14 is installed, so check that PyO3 and its build tool support it.

**Blocked by:** None — can start immediately

**Status:** ready-for-agent

- [ ] The engine is always either over or waiting on exactly one Decision for one Player. Picking an Option by index moves it forward, and a pick carrying a stale Decision sequence number is rejected.
- [ ] The Python engine module can:
  - create a Game from settings and a seed;
  - create a Game from a Scenario (Generation, Global Parameters, and each Player's MegaCredits, Production and Terraform Rating);
  - read the current Decision and its Options (index, label, structured details);
  - pick an Option;
  - return a Player View;
  - read the game log;
  - report when the Game is over, with a score for each Player.
- [ ] Test helpers let a test build a Scenario in a few readable lines and pick an Option by matching its label or details.
- [ ] Scenario tests cover:
  - Asteroid's cost and effect;
  - Asteroid not offered when it is unaffordable, or when Temperature is maxed (follow the rules authority order and record the call in the rules notes);
  - one or two Actions per Turn;
  - Passing for the rest of the Generation;
  - Production income;
  - the end of the Game.
- [ ] The server runs locally, attaches a human or Random Bot Controller to each Player, and streams updates (the Decision, the Player View, new game log lines) over the WebSocket.
- [ ] A WebSocket smoke test plays a Random Bot vs Random Bot Game to the end.
- [ ] A human can play a full Game against a Random Bot in the browser and see the final scores.
- [ ] The project README gives one command each to run the tests and to start the server with the GUI.
