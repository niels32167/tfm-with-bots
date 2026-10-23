# Terraforming Mars

A digital version of the board game Terraforming Mars, built so an AI opponent can be trained against it by self-play. Game terms follow the official rulebook; the terms under "Playing the game" are this project's own.

## Language

### The game

**Game**:
One complete play of Terraforming Mars on the Tharsis board, from setup to final scoring.

**Generation**:
One round of a Game, made of the Player Order, Research, Action and Production phases.
_Avoid_: round, turn

**Turn**:
One Player's go during the Action phase, in which they take one or two Actions or pass.

**Action**:
One thing a Player does on their Turn: play a card, use a Standard Project, claim a Milestone, fund an Award, use a card's action, convert plants or heat, or similar.
_Avoid_: move, step

**Pass**:
Ending your part in the Action phase for the rest of the Generation.

**Draft**:
The Research-phase variant where Players pick cards one at a time from hands passed between them, instead of each drawing four. On by default in this project.

**Corporate Era**:
The rules and extra cards in the base box marked with the Corporate Era symbol. Every Game in this project uses them.

### Mars

**Global Parameter**:
One of the three conditions on Mars that Players raise: Temperature, Oxygen and Oceans. The Game ends after the Generation in which all three reach their maximum.

**Terraform Rating**:
A Player's score for terraforming, raised by one for each step of a Global Parameter they raise. It is also part of their income and their Victory Points.
_Avoid_: TR (in prose), rating

**Area**:
One hexagonal place on the board that can hold a Tile. Some Areas are reserved for Ocean Tiles; many give a placement bonus.
_Avoid_: hex, space, field

**Tile**:
A piece placed on an Area: an Ocean, a Greenery, a City, or a special Tile printed with its card's symbol.

### Players and cards

**Player**:
One of the 2–5 competitors in a Game, with their own Corporation, resources, Production, cards and Tiles.
_Avoid_: seat

**Resource**:
One of the six standard goods a Player stockpiles: MegaCredits, steel, titanium, plants, energy and heat.

**Card Resource**:
A marker kept on a card rather than with the Player, such as animals, microbes, science or fighters.
_Avoid_: resource (on its own)

**Production**:
How much of each Resource a Player gains in every Production phase.
_Avoid_: income (except MegaCredits income, which is MegaCredit Production plus Terraform Rating)

**Corporation**:
The card each Player starts the Game with, giving their starting MegaCredits and a special ability.

**Project Card**:
A card Players buy and play: Automated (green), Active (blue) or Event (red).

**Tag**:
A symbol on a card, such as building, space or science, that card costs, requirements and effects refer to.

**Requirement**:
A condition that must hold before a card can be played, such as a minimum Oxygen level or a number of Tags.

**Card catalog**:
The printed data of every card in the Game's card set: name, number, type, cost, Tags, Requirements, Victory Points and text. It is the same in every Game; a Game refers to its cards and never holds copies of them.
_Avoid_: card list (the fan-made website the printed data is imported from), card database

**Standard Project**:
An Action every Player can always take for a fixed price, such as building a City or an Ocean.

**Milestone**:
A goal a Player can claim for 8 MegaCredits once they meet it, worth 5 Victory Points. Only three can be claimed per Game.

**Award**:
A category a Player can fund for 8, 14 or 20 MegaCredits. At the end, the leader gets 5 Victory Points and the runner-up 2 (not in 2-player Games). Only three can be funded per Game.

### Playing the game

**Decision**:
The one choice the Game is waiting for, from one Player, at any moment. A compound Action (play a card, then pay, then place a Tile) is a chain of Decisions.
_Avoid_: prompt, request, input

**Option**:
One of the finite answers a Decision offers.
_Avoid_: action, move, choice

**Controller**:
Whoever answers a Player's Decisions: a human at the screen, a Random Bot, or later a trained AI.
_Avoid_: agent (for the general case), seat

**Random Bot**:
A Controller that picks one of the offered Options at random.

**Player View**:
Everything one Player is allowed to know: their own hand, all public information, and the cards they passed in the Draft. Never another Player's hand or the deck order. AI Controllers see only the Player View.
_Avoid_: observation, visible state

**Scenario**:
A described position to start a Game from instead of normal setup, such as "Oxygen at 5 %, this Player holds these cards and 30 MegaCredits". Used by tests and the dev panel's state editor.
_Avoid_: fixture, test state, setup

**Replay**:
A Game's settings and seed (or Scenario) plus the Options picked, in order. It reproduces the Game exactly.
_Avoid_: save state, log (the game log is the human-readable history)

**Hotseat**:
Several human Controllers sharing one screen. All hands are visible, since it is a testing setup.

## Flagged ambiguities

- "Action" means the game's Action (above). The reinforcement-learning sense of "action" (one thing the AI picks) is an **Option**.
