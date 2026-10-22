Status: ready-for-agent

# Spec: Phase 1 — a playable, fast Terraforming Mars for rules testing

## Problem Statement

I want to train an AI opponent for Terraforming Mars by self-play. That needs a game engine that is both correct and very fast, and nothing available today is both. The open-source web version is too heavy to run millions of Games. A fast engine I can't verify is worthless for training, because the AI would learn whatever rule bugs it has.

Before any AI work starts, I need to sit down and play complete Games against bots or against myself, in an interface that is pleasant to use, and come away trusting that the rules work the way the rulebook says.

## Solution

Phase 1 delivers a complete digital Terraforming Mars: the base box with Corporate Era, on the Tharsis board, for 2–5 Players, with Draft on by default.

- **A fast Rust engine, used from Python.** Every choice is a Decision with a list of Options. Every Game is reproducible from its Replay, and game states copy cheaply.
- **A polished browser GUI**, laid out like Board Game Arena's Terraforming Mars. Each Player is controlled by a human or a Random Bot. A dev panel (game log, seed, undo, save/load, Replay step-through, state editor) helps hunt down rule bugs.
- **Tests that build confidence before play-testing**: a scenario test for every card, scenario tests for the core rules, and 100,000 fuzzed Random Bot Games.

Phase 1 is done when all four of these hold:
- every card is implemented and tested;
- 100,000 fuzzed Games run clean;
- the speed target is met;
- I have played three full Games in the GUI without finding a rule bug.

## User Stories

### Setting up a Game

1. As a player, I want to start a new Game with 2–5 Players, so that I can test any table size the rules support.
2. As a player, I want to set each Player's Controller to human or Random Bot, so that I can play against bots, play every seat myself in Hotseat, or watch bots play.
3. As a player, I want Draft on by default with a switch to turn it off, so that I play the way I usually do but can still test the standard Research rules.
4. As a player, I want to enter a seed or get a random one, so that I can replay an interesting or broken Game exactly.
5. As a player, I want to be dealt two Corporations and ten Project Cards, then choose one Corporation and buy any of the cards for 3 MegaCredits each, so that setup follows the Corporate Era rules.
6. As a player, I want to see each Corporation's starting MegaCredits and ability before choosing, so that I can choose with full information.
7. As a player, I want Players to start with no Production except what their Corporation gives, so that the Corporate Era starting rules apply.
8. As a player, I want the first Player picked from the seed and shown clearly, so that I know who starts.

### Generations and phases

9. As a player, I want the first-player marker to move to the next Player each Generation, so that turn order rotates as in the rules.
10. As a player, I want each Research phase from Generation 2 onwards to deal four cards to each Player, so that I can buy new cards.
11. As a player with Draft on, I want to keep one card at a time from a hand and pass the rest, with the passing direction alternating by Generation as the rules say, so that Draft plays like it does at the table.
12. As a player with Draft on, I want to be able to see which cards I passed to whom, so that I know what my opponents might hold.
13. As a player, I want to buy any number of my Research cards for 3 MegaCredits each and discard the rest, so that the Research phase completes.
14. As a player, I want the Research and Draft choices of other Players kept hidden from me, even though the engine takes them one Player at a time, so that hidden information stays hidden.
15. As a player, I want the Action phase to give Players Turns in order, each taking one or two Actions or Passing, so that the core loop matches the rulebook.
16. As a player, I want to end my Turn after one Action without Passing, so that I can wait and react to others.
17. As a player, I want Passing to take me out of the Action phase for the rest of the Generation while the others carry on, so that the passing rule is enforced.
18. As a player, I want the Production phase to turn energy into heat, then give me MegaCredits equal to Terraform Rating plus MegaCredit Production, and every other Resource equal to its Production, so that income is correct.
19. As a player, I want the current Generation shown at all times, so that I know how far the Game has gone.

### Actions

20. As a player, I want to play a Project Card from my hand when I meet its Requirements and can pay its cost, so that I can build my engine.
21. As a player, I want to be offered only the cards I can actually play, so that I can't make illegal moves.
22. As a player, I want to pay with steel (worth 2) for cards with a building Tag and titanium (worth 3) for cards with a space Tag, plus any card or Corporation effect that changes those values or lets me pay with another Resource, so that the payment rules are complete.
23. As a player, I want to choose how a payment is split between MegaCredits, steel, titanium and any other allowed Resource, so that I control what I keep.
24. As a player, I want cost discounts from my cards and Corporation applied automatically, so that I don't have to work them out.
25. As a player, I want cards that relax or ignore Global Parameter Requirements to be respected, so that those cards work.
26. As a player, I want to use any Standard Project (Sell Patents, Power Plant, Asteroid, Aquifer, Greenery, City) at its printed price, so that I always have something to do.
27. As a player, I want Sell Patents to let me pick cards from my hand one at a time and stop when I'm done, so that I sell exactly what I want.
28. As a player, I want to convert 8 plants into a Greenery Tile and 8 heat into a temperature step, with cards that change those amounts respected, so that conversions work.
29. As a player, I want to claim a Milestone for 8 MegaCredits once I meet it, as long as fewer than three have been claimed, so that Milestones work.
30. As a player, I want to fund an Award for 8, 14 or 20 MegaCredits depending on how many are already funded, as long as fewer than three are funded, so that Awards work.
31. As a player, I want to use each Active card's action once per Generation, so that blue cards work.
32. As a player, I want effects that offer a choice ("do this or that") to ask me which, so that I decide.
33. As a player, I want effects that target another Player, such as removing their plants, to let me pick the target, including the choices the rules allow when nobody has anything to lose, so that attacks work as printed.

### Tiles and the board

34. As a player, I want to choose an Area for every Tile I place, from only the Areas where it is allowed, so that placement is correct and easy.
35. As a player, I want Ocean Tiles to go only on Areas reserved for oceans, so that the map works.
36. As a player, I want my Greenery Tiles placed next to one of my own Tiles whenever that's possible, so that the greenery placement rule is enforced.
37. As a player, I want Cities kept off ocean Areas and away from other Cities, so that the city placement rule is enforced.
38. As a player, I want the named reserved Areas (Noctis City, plus the off-Mars Phobos Space Haven and Ganymede Colony) used only by their cards, so that those cards work.
39. As a player, I want the placement bonus printed on an Area (steel, titanium, plants or cards) when I place a Tile there, so that placement choices matter.
40. As a player, I want 2 MegaCredits for each Ocean Tile next to a Tile I place, so that ocean adjacency pays.
41. As a player, I want special Tiles from cards placed under their cards' own rules, so that those cards work.
42. As a player, I want to see who owns each Tile, so that I can plan adjacency and Awards.

### Global Parameters and Terraform Rating

43. As a player, I want each step I raise a Global Parameter to give me one Terraform Rating, so that terraforming is rewarded.
44. As a player, I want Greenery Tiles to raise Oxygen one step while it is below its maximum, so that greeneries terraform.
45. As a player, I want the track bonuses applied when they are reached: heat Production at the two marked temperature steps, an Ocean Tile at 0 °C, and a temperature step at 8 % Oxygen, so that the track bonuses work.
46. As a player, I want a Global Parameter at its maximum to stop rising, while still letting me play cards that would raise it as the rules allow, so that late-game play is correct.
47. As a player, I want Temperature, Oxygen and the number of Oceans placed shown on tracks like those in the reference layouts, so that I can read the state of Mars at a glance.

### Cards

48. As a player, I want all 208 Project Cards and every Corporation in the base box to work as printed, so that I play the full game.
49. As a player, I want ongoing effects on my Active cards and Corporation to trigger when their condition happens, such as any Player playing a Tag or placing a Tile, so that engines work.
50. As a player, I want Card Resources (animals, microbes, science, fighters) added to and removed from cards and counted for Victory Points as printed, so that those cards work.
51. As a player, I want Event cards to lie face down after use with their Tags no longer counting, so that Tag counts are correct.
52. As a player, I want MegaCredit Production allowed down to −5 and all other Production kept at 0 or more, so that Production limits are enforced.
53. As a player, I want the deck reshuffled from the discard pile when it runs out, so that the Game never stalls.

### End of Game and scoring

54. As a player, I want the Game to end after the Generation in which all three Global Parameters reach their maximum, so that the end condition is right.
55. As a player, I want a chance to convert plants into Greeneries in player order after the final Production phase and before scoring, so that the final conversion rule applies.
56. As a player, I want a final score screen showing each Player's Terraform Rating, Milestones, Awards, Greeneries, Cities and card Victory Points, so that I can check the scoring.
57. As a player, I want Awards to give 5 Victory Points to the leader and 2 to the runner-up, with ties handled as the rules say and no runner-up in 2-player Games, so that Awards score correctly.
58. As a player, I want each City to score 1 Victory Point per adjacent Greenery, whoever owns it, so that city scoring is right.

### GUI: look and feel

59. As a player, I want the screen laid out like Board Game Arena's Terraforming Mars, so that it feels like the version I like.
60. As a player, I want the Mars board drawn over a globe image with every Area, placement bonus and Tile visible, so that the board is both attractive and readable.
61. As a player, I want a Standard Projects panel and a Milestones and Awards bar showing prices and what is claimed or funded, so that I can see what's available.
62. As a player, I want a board for each Player showing Resources, Production and Terraform Rating, so that I can compare Players.
63. As a player, I want cards drawn in the style of the fan-made card list, with cost, Tags, Requirements, Victory Points, effect icons and text, so that every card is readable without artwork.
64. As a player, I want to hover over or click a card to see it enlarged, so that I can read the small text.
65. As a player, I want my hand and each Player's played cards shown, grouped by card type with Card Resources visible, so that I can see everyone's engine.
66. As a player, I want the current Decision shown in a status bar with its Options as buttons, and Options that refer to Areas or cards highlighted where they are, so that I always know what to do and can click the board directly.
67. As a player, I want a payment picker for splitting a cost, so that I don't scroll through a long list of payment Options.
68. As a player, I want Random Bot Turns played at a pace I can follow, with a speed control, so that I can see what they do.
69. As a player, I want a game log describing in plain language everything that has happened, so that I can follow and check each step.
70. As a player in Hotseat, I want to see all hands, so that I can test freely.
71. As a player against Random Bots, I want to see only my own Player View, so that hidden information stays hidden.
72. As a player, I want the whole thing to run locally on my machine in a desktop browser, so that it doesn't depend on any website being up.

### Dev panel

73. As a rules tester, I want to toggle a dev panel on and off, so that the polished view stays clean while I can still debug.
74. As a rules tester, I want to see and copy the Game's seed, so that I can report and replay it.
75. As a rules tester, I want to undo back to my previous Decision as many times as I like, so that I can try alternatives.
76. As a rules tester, I want to save the current Game as a Replay file and load it later, so that I can continue it or keep it as evidence of a bug.
77. As a rules tester, I want to step through a loaded Replay forwards and backwards, so that I can find the exact moment a rule went wrong.
78. As a rules tester, I want to edit the state (give a Player Resources or Production, set Global Parameters, put a specific card in a hand, place a Tile, set the Generation), so that I can set up a situation for a card without playing for an hour.
79. As a rules tester, I want an edited state to be a Scenario that I can save and reload like any Replay, so that test setups can be reused and turned into automated tests.
80. As a rules tester, I want to see the full state in the dev panel, including all hands and the deck order, so that I can check how hidden information is handled.
81. As a rules tester, I want every rules judgment call listed in a rules-notes document, so that I can check play against the agreed interpretation.

### Engine module (for tests and the future AI)

82. As an AI developer, I want to create a Game from settings and a seed in Python, so that training can run Games.
83. As an AI developer, I want to read the current Decision (which Player, what kind) and its Options in Python, so that a Controller can choose.
84. As an AI developer, I want to pick an Option by its index and get the next Decision, so that one simple loop plays a whole Game.
85. As an AI developer, I want each Option to carry structured details (card, Area, Player, amounts) as well as a readable label, so that a network can encode it and the GUI can display it.
86. As an AI developer, I want a Player View for any Player that never includes other Players' hands or the deck order, so that a trained AI plays fair.
87. As an AI developer, I want to copy a Game in microseconds, fully independent of the original, so that tree search stays possible later.
88. As an AI developer, I want to play a Game out to the end with random Options inside the engine, so that benchmarks and later search rollouts are fast.
89. As an AI developer, I want at least 1,000 complete 2-player Random Bot Games per second across my 16 cores, so that training is fast enough.
90. As an AI developer, I want the final score breakdown per Player when a Game ends, so that I can compute rewards.
91. As an AI developer, I want the same Replay always to produce the same Game on any machine, so that experiments and bugs are reproducible.
92. As a developer, I want to start a Game from a Scenario, so that tests and the state editor share one way of setting up situations.
93. As a developer, I want the card catalog (the printed data for every card) available from the engine module, so that the GUI renders cards from the same data the engine uses.

### Card data

94. As a developer, I want the printed card data imported from the fan-made card list into our own card file, so that nobody types in 208 cards by hand.
95. As a developer, I want the imported data compared with the open-source game's card definitions and every mismatch listed, so that typos are caught and settled using the rules authority order.
96. As a developer, I want the card list's icon images stored in the project, so that card rendering doesn't depend on that website staying up.

### Confidence

97. As a developer, I want every Project Card and Corporation to have at least one scenario test, so that each card's behaviour is checked.
98. As a developer, I want 100,000 fuzzed Random Bot Games to run without crashes or broken invariants, so that rare rule interactions get exercised.
99. As a developer, I want every failing fuzzed Game saved as a Replay, so that it can be reproduced and turned into a test.
100. As a developer, I want a one-command speed benchmark that reports Games per second and copy time, so that the speed target is checked continuously.
101. As a player, I want to play three complete Games in the GUI without finding a rule bug before AI work starts, so that I trust the engine.

## Implementation Decisions

### Shape of the system

- There are four parts, each depending only on the one before it: Rust engine → Python engine module (PyO3 bindings) → local Python server (FastAPI with a WebSocket) → React and TypeScript GUI in the browser (ADRs 0006, 0007, 0008).
- Tests, the server and the future AI all use the Python engine module. Nothing else reaches into the engine.
- One card file holds two kinds of data for every card:
  - printed data imported from the fan-made card list (ADR 0005);
  - our own hand-written effect data for simple effects (ADR 0009).

  Triggers, ongoing effects, card actions and unusual cards are written in Rust.
- Rules authority: the official rulebook, then the official FryxGames FAQ and corrections, then the open-source game's behaviour as tiebreaker (ADR 0001). Every judgment call goes into a rules-notes document in the docs folder.

### Engine

- **Decisions (ADR 0002).**
  - At any moment the engine is either over or waiting on exactly one Decision for one Player.
  - It moves forward only when an Option is picked by index.
  - Each Decision carries a sequence number, so stale picks (for example a double click in the GUI) are rejected.
- **Decision kinds.** This list may grow:
  - choose Corporation;
  - buy initial Project Cards;
  - Draft pick;
  - buy Research cards;
  - choose an Action, end the Turn, or Pass;
  - choose a payment;
  - choose an Area;
  - choose a target Player;
  - choose a card to receive a Card Resource or an effect;
  - choose between alternatives in an effect;
  - choose cards to sell or discard;
  - final Greenery conversion.
- **Picking several things.** Decisions where a Player picks several items (buying, selling, discarding) are chains of single picks with a "done" Option.
- **Simultaneous steps.** Corporation choice, initial buys, Draft and Research are taken one Player at a time in player order. A Player's choices stay out of other Players' Player View until the rules reveal them.
- **Legal Options only.** Options are only ever legal moves. Every Decision has at least one Option.
- **Payment.** There is one Option for each distinct legal way to split the payment. The GUI groups them into a payment picker.
- **Game state (ADR 0004).** The state is flat and self-contained, with no shared references, so copying a Game is a plain value copy.
- **Determinism (ADR 0010).**
  - The Game state holds one seeded random number generator, used for every shuffle.
  - No randomly ordered collection, clock reading or other outside input may influence the rules.
- **Replays.**
  - A Replay is the settings, the seed (or a Scenario) and the Options picked.
  - Undo and Replay step-through work by replaying to an earlier point, or by restoring a copy.
- **Views.**
  - The Player View is structured and serializable.
  - A full view, showing all hands and the deck order, exists for Hotseat and the dev panel.
- **Random playout.** A Random Bot playout runs inside the engine. It is used by the speed benchmark, and later by search.
- **Game log.** The engine produces the game log as plain-language event lines, one or more per resolved Option.
- **Effect primitives.** The effect data uses a small set of primitives:
  - gain or lose Resources;
  - change Production;
  - place a Tile;
  - raise a Global Parameter;
  - draw cards;
  - add or remove Card Resources;
  - gain Terraform Rating.

  Requirement checks, cost discounts and Tag counting live in one central place, not inside each card.

### Python engine module (the test seam)

The module offers these operations:
- create a Game from settings (Player count, Draft on or off, seed);
- create a Game from a Scenario;
- read the current Decision: the Player, the kind, the sequence number, and the Options, each with an index, a label and structured details;
- pick an Option by index;
- get the Player View for a Player, or the full view;
- copy a Game;
- export a Replay, load one, and rebuild the Game at any step of a Replay;
- check whether the Game is over, and get the final score breakdown;
- run Random Bot playouts;
- read the game log;
- read the card catalog.

Data crosses the boundary as plain, JSON-serializable Python values, which the server forwards unchanged. A compact numeric encoding for training is phase-2 work.

### Scenario

A Scenario describes:
- the settings and the Generation;
- the phase and whose Turn it is;
- the Global Parameters;
- the Tiles on Areas;
- the Milestones claimed and Awards funded;
- each Player's Corporation, Resources, Production, Terraform Rating, hand, and played cards with their Card Resources;
- the deck order, or a seed to shuffle it.

Anything left out takes normal defaults. Tests and the dev panel's state editor both build Games from Scenarios, and a Scenario is saved inside a Replay like any other starting point.

### Python server

- It runs locally only, holds Games in memory, and attaches a Controller (human or Random Bot) to each Player. Random Bot moves are played with an adjustable delay.
- Messages from the GUI to the server:
  - new Game (settings and Controllers);
  - pick Option (sequence number and index);
  - undo;
  - save Replay;
  - load Replay;
  - step through a Replay;
  - edit state (as a Scenario);
  - toggle the full view.
- Messages from the server to the GUI:
  - an update: the current Decision when a human must answer it, the view, new game log lines, and whether undo is available;
  - Game over, with the score breakdown;
  - errors.
- Which view the GUI gets: the full view in Hotseat or with the dev panel's full view turned on; otherwise the human Player's Player View.

### GUI

- React and TypeScript.
- **Layout.** It is modelled on Board Game Arena's Terraforming Mars, after studying its game view in the browser pane. The user logs in there themselves if a page needs it. The Asmodee digital game's screenshot is a second reference for the tracks.
- **Board.** Areas are drawn as SVG over a public-domain NASA Mars image. Around it go:
  - the Oxygen arc;
  - the thermometer with its bonus markers;
  - the Ocean counter;
  - the Generation;
  - the Standard Projects panel;
  - the Milestones and Awards bar.
- **Main screen** also shows:
  - player boards with Resources and Production;
  - the hand, and each Player's played cards;
  - the status bar showing the Decision and its Options;
  - board and card highlights for Options;
  - the payment picker.
- **Other screens:** the Draft view, the final score screen, and the dev panel.
- **Cards** copy the card list's layout and icons, using the card catalog from the engine module.

### Build order (vertical slices)

1. **Walking skeleton.**
   - Engine: Generations, Production, Global Parameters and their bonuses, Tiles on Tharsis, Standard Projects except Sell Patents, plant and heat conversion, Milestones, Awards, end of Game and scoring. Players start without Corporations or cards for now.
   - Around it: the Python module, the server, and the GUI board, player boards and status bar.
   - Tooling: the Random Bot, basic dev panel (seed, game log, undo, save/load), and the fuzzing and benchmark harness.
2. **Card groundwork.**
   - Card import and catalog, card rendering, hand and played cards.
   - Corporations and setup choices, the Research phase and Draft, Sell Patents.
   - Payment Decisions, Requirements, Tag counting.
3. **Cards in batches, grouped by mechanism.** Each batch lands with its scenario tests and is playable straight away. The batches are:
   - simple Automated cards driven by effect data;
   - Events;
   - Active cards with actions;
   - ongoing triggers;
   - Card Resources;
   - special Tiles and reserved Areas;
   - attacks;
   - the remaining unusual cards.
4. **Polish and exit.**
   - Full dev panel: Replay step-through and state editor.
   - Visual polish towards Board Game Arena's look.
   - The exit checks: the 100,000-Game fuzz run, the benchmark, and three play-test Games.

## Testing Decisions

- **A good test goes through the Python engine module only.** It sets up a Scenario or seed, picks Options, and checks what an outsider can see: the Options offered, the Player View, the game log or the score. Tests never inspect engine internals, so the Rust code can be restructured freely.
- **Tests read like play.** A small Scenario-building helper and a "pick the Option whose label or details match" helper keep tests short and readable to someone who knows the rules. Test names use the glossary's terms.
- **What gets tested:**
  - **Every card.** Each Project Card and Corporation has at least one scenario test covering its Requirements, its effect and its Victory Points.
  - **Core rules.** Scenario tests cover:
    - the order of Generations and phases, and Draft passing;
    - Production;
    - each Standard Project, and the plant and heat conversions;
    - Tile placement rules, placement bonuses and ocean adjacency;
    - Global Parameter bonuses and maximums;
    - Milestones, including the limit of three;
    - Awards, including ties and the 2-player rule;
    - the end of the Game, the final Greenery conversion, and scoring.
  - **Legality.** Scenarios at the edges check that illegal Options are never offered: a cost the Player can't afford, an unmet Requirement, the Milestone limit reached, no legal Area left.
  - **Hidden information.** The Player View never contains another Player's hand or the deck order, including during Draft.
  - **Reproducibility.** The same Replay gives an identical Game and game log, and a copied Game is independent of the original.
  - **Fuzzing.**
    - What runs: Random Bot Games with 2–5 Players, Draft on and off.
    - Checks after every Decision:
      - no negative Resources;
      - Production within its limits;
      - Global Parameters within range;
      - Tiles only on legal Areas;
      - at most three Milestones claimed and three Awards funded;
      - card count conserved across deck, discard, hands, played cards and Draft;
      - every Decision has at least one Option.
    - Checks per Game: it ends within a generous Generation limit (a fuzzing guard, not a rule), and the final score breakdown adds up.
    - Every failure is saved as a Replay.
    - A short run of about 1,000 Games is part of the normal test suite. The full 100,000-Game run is the phase-1 exit check.
  - **Speed.** A benchmark runs Random Bot playouts through the module and must reach 1,000 2-player Games per second across 16 cores. It also reports how long a copy takes, and, for information only, how many Decisions per second a Python loop achieves.
  - **Server.** One WebSocket smoke test starts a Game with Random Bots for every Player and receives updates until the Game is over.
  - **GUI.** Checked by playing: by the user, and by Claude in the browser preview while building. There are no automated GUI tests.
  - **Card data.** The import is compared against the open-source game's card definitions, and mismatches are listed for review. This is a check, not a pass/fail test.
- **Prior art.** None yet; this is the project's first code. The first card tests set the pattern that all later ones copy.

## Out of Scope

- All AI work: rewards, network design, training, a compact numeric encoding of the Player View, and playing against a trained AI. That is phase 2.
- Tree search. Only its precondition, cheap copies, is in scope.
- Solo mode, Prelude, Venus Next, Colonies, Turmoil, promo cards, and the Hellas and Elysium boards (ADR 0003).
- Card illustrations.
- Public release, online or cross-machine multiplayer, accounts, a mobile layout, sound and translations.
- Move-by-move comparison against the open-source game's engine.
- Undo outside the dev panel, and turn timers.

## Further Notes

- **Steps that need the user's OK when reached:**
  - installing the Rust toolchain (rustup);
  - downloading the card list's icons (about 100 small files) and the NASA Mars image;
  - installing Python and npm packages.
- **Python version.** Python 3.14 is installed. Confirm at setup that PyO3 and the build tool support it. PyTorch is only needed in phase 2.
- **Card count.** The card list confirms 208 Project Cards (#001–#208): 137 from the base game and 71 Corporate Era.
- **Asmodee screenshot.** The user's screenshot of the Asmodee digital game exists only in the conversation. If it should be kept as a reference, the user needs to save it into the project.
- **Who reads the code.** The user mostly writes Python. The Rust code should stay plain and readable, and the Python tests are the readable statement of the rules.
- **Domain docs.** The glossary is in CONTEXT.md, and the decisions are in ADRs 0001–0010. This spec contradicts none of them.
