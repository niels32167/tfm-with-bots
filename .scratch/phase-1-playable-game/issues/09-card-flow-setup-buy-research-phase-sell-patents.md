# 09 — Card flow: setup buy, Research phase, Sell Patents

**What to build:** How cards move through a Game:
- **Setup.** Each Player is dealt 10 Project Cards and buys any of them for 3 MegaCredits each. Starting MegaCredits stay at the temporary fixed amount until Corporations arrive in ticket 21.
- **Research phase.** From Generation 2 onwards, each Player draws 4 cards and buys any of them for 3 each; the rest are discarded.
- **Hidden choices.** Buying is done one Player at a time in player order (ADR 0002) and stays hidden from the other Players.
- **Sell Patents.** The Standard Project lets a Player pick cards one at a time, then "done", for 1 MegaCredit each.
- **Reshuffle.** When the deck runs out, the discard pile is reshuffled into a new deck.
- **Player View.** It never contains another Player's hand or the deck order.

The GUI gets the buying screens and Sell Patents.

**Blocked by:** 08 — Playing Project Cards

**Status:** ready-for-agent

- [x] The setup buy and the Research phase work for 2–5 Players and appear in the GUI.
- [x] Test: during buying, no Player View contains another Player's hand, choices or the deck order.
- [x] Sell Patents works as a chain of single picks ending with "done".
- [x] Test: the deck reshuffles from the discard pile when it is empty.
- [x] The fuzzer gains a card-count invariant: deck, discard pile, hands and played cards always add up to the full card set.
- [x] Every rule above has a scenario test.

## Comments

### 2026-10-24 — implemented (Claude)

**Decisions made with the user** (one round of questions; every recommended option was chosen):
- **Buying stays hidden until every Player is done.**
  - Each Player picks "Buy …" one card at a time, then Done.
  - Nothing is paid and no card moves until the last Player is done. Then every Player pays,
    takes the cards bought into their hand, and the rest go face down to the discard pile.
  - The log then says how many cards each Player bought, never which.
- **Decision kinds and Options:**
  - `"buy_cards"` (setup and Research) and `"sell_patents"`.
  - Details: `{"type": "buy_card", "card": "mine", "cost": 3}`,
    `{"type": "sell_card", "card": "mine", "megacredits": 1}`, Sell Patents as
    `{"type": "standard_project", "project": "sell_patents", "cost": 0}`, and the generic
    `{"type": "done"}`.
- **The discard pile lies face down:** Player Views have `discard_size` only; the full view also
  lists `discard`.
- **What a new Game deals:**
  - By default the real rules: 10 cards each from the whole shuffled deck.
  - A Game setting, `implemented_cards_first`, puts the implemented cards (shuffled) on top of
    the deck. The GUI's setup screen has a checkbox for it, on by default. Replays keep it.
- **Setup cards cost 3 MegaCredits each,** with 42 MegaCredits as a plain stand-in until ticket 21.
  Research showed the Beginner Corporation does keep its 10 cards free (its open-source card:
  "Instead of choosing from 10 cards during setup, you get 10 cards for free"), but ticket 21
  leaves the Beginner out.
- **GUI:**
  - Buying happens in a panel over the board, with the cards as large as the space in view
    allows.
  - The hand moves into a dock at the bottom of the window.
  - Sell Patents is picked in that dock.
- **The Research phase** deals 4 cards, with no Draft until ticket 10.

**Calls made by Claude** (recorded in `docs/rules-notes.md` under "Card flow"):
- **Who is asked to buy:** a Player is asked only while they can buy another card. Someone who
  cannot afford one, or has bought every card dealt, is passed over without a Decision.
- **Sell Patents:**
  - offered whenever the hand holds a card;
  - each card sold gains 1 MegaCredit at once;
  - Done comes only after the first sale;
  - selling the last card ends the Action.
- **When the deck runs out:** the discard pile is reshuffled when a card must be drawn from the
  empty deck. With both empty, the Player draws nothing.
- **Test seams:** the Python engine module throughout (`tests/rules/`, `tests/engine/`), the fuzz
  invariants, and the server WebSocket for the new setting and the Random Bot's buying.
- **The fuzzer** deals the implemented cards first for seeds 4–7, 12–15 and so on.
- **A Random Bot in the GUI buys without pausing,** so the time spent waiting for it says nothing
  about how many cards it bought (see the code review).

**Design notes:**
- **Engine:**
  - `engine/src/card_flow.rs` (`impl Game`) holds:
    - the deal (`begin_setup`, `begin_research_phase`);
    - buying (`can_buy`, `buying_options`, `buy`, `done_buying`, `finish_buying`);
    - Sell Patents (`selling_options`, `sell`, `finish_selling`);
    - drawing with the reshuffle (`draw`, `draw_cards`).
  - `Player::buying` is a `Buying { dealt, bought }`, two `CardSet`s; `Game::discard` is a
    `CardSet` and `Game::selling` counts the cards sold so far.
  - A Game is still a plain value copy (ADR 0004), and the reshuffle uses the Game's own random
    numbers (ADR 0010).
  - `Phase` gains `Setup` and `Research`; the view's `phase` reads `"setup"` and `"research"`.
  - `Game::new` draws the first player, shuffles the deck and starts the setup buy. "Generation 1
    begins" comes once everyone is done.
  - From Generation 2 the Production phase leads to "Generation n begins", then the Research phase.
  - A Scenario still starts in the Action phase.
  - `Game::player_order()` and `first_in_player_order_who()` serve the deal, the reveal, buying
    and the final Greenery conversion.
  - `StandardProject::ALL` now starts with Sell Patents, as printed. `STARTER_SET` and
    `deal_starter_set` are gone.
  - `Deck::shuffled_from(cards)` builds a shuffled deck of exactly those cards.
- **New log lines:**
  - "Setup: each Player is dealt 10 Project Cards and may buy any of them for 3 MegaCredits each.";
  - "Research phase: each Player draws 4 cards and may buy any of them for 3 MegaCredits each.";
  - "Player 2 buys 1 of their 4 cards for 3 MegaCredits." (and "buys none of …", "buys all 4 of
    their cards …");
  - "Player 1 sells 2 patents for 2 MegaCredits.";
  - "The deck has run out, so the discard pile is shuffled into a new deck of 12 cards.";
  - "The deck and the discard pile are empty, so Player 1 draws no more cards."
- **View:**
  - Each player board has `buying` (`{"dealt", "bought"}`), only in its own Player View and the
    full view, and only while Players buy.
  - The view has `discard_size`, and `discard` in the full view only.
- **Scenarios** take a top-level `"discard"` list of card ids.
- **Python:**
  - `tm_engine.Game(seed=…, players=…, implemented_cards_first=False)`.
  - The server's `new_game` message takes `implemented_cards_first`.
  - Test helpers: `buying()`, `buy()`, `skip_buying()` and `end_the_action_phase()`.
    `end_the_generation()` now also gets every Player through the next Research phase without
    buying.
- **Tests:**
  - `tests/rules/test_buying_cards.py` (setup and Research, 2–5 Players) and
    `tests/rules/test_sell_patents.py`;
  - the discard pile, reshuffle and deal setting in `tests/rules/test_deck.py`;
  - hidden information at setup and in a Research phase in `tests/engine/test_views.py`;
  - the server's setting and Random Bot buying in `tests/server/test_new_game.py`;
  - 483 tests in all.
- **Fuzzer:**
  - `every_card_in_exactly_one_place` covers the deck, the discard pile, hands, played cards and
    the cards dealt to buy from, with sizes that agree.
  - It also checks that the cards bought are among those dealt, and that only the setup and
    Research phases have them.
  - `players_for` became `settings_for`.
- **GUI:**
  - `gui/src/cards/BuyingPanel.tsx` covers the board while Players buy:
    - the cards dealt, sized by `useFitZoom` to fit above the dock without scrolling (10 cards
      fit at 1024×768 and 1440×900);
    - click a card to buy it; those bought get a green "Bought" ribbon;
    - hovering enlarges a card to read it;
    - "Look at the board" hides the cards;
    - it says whom it is waiting for.
  - `gui/src/cards/HandDock.tsx` is the hand, fixed to the bottom of the window:
    - only the cards' tops show, and hovering lifts a card into full view;
    - cards that can be played are outlined, and in Sell Patents the cards to sell are outlined
      in red;
    - in the full view it has a tab for each Player's hand, following the Player deciding;
    - it folds to one line, and unfolds when a new Decision lets a card in it be played or sold.
  - `PlayerCards` became `PlayedCards` (played cards only, below the board).
  - Mars and the thermometer now shrink together (`--mars-size`) to leave room for the dock, so
    the Milestones and Awards bar stays in view at 1440×900.
  - The status bar explains buying and selling. Buy and sell Options are picked on the cards, and
    Done stays a button.
- **Game length and speed:**
  - A 2-player Random Bot Game is now about 510 picks and 25 Generations (750 picks and 16
    Generations with 5 Players), up from about 190, because bots buy and sell cards. This is still
    short of ADR 0004's "roughly 800 Decisions" with Draft; ticket 10 adds the Draft.
  - Benchmark, on battery with the power-saver profile:
    - before the code review: 89,825 Games/s on 16 processes and 8,300 in 1;
    - after it, at 31 % battery with the cores at 1.4 GHz: 54,229–55,417 on 16 and 3,003 in 1.
      The review's changes touch nothing that runs more than a few times per Generation, so this
      is the power state.
    - Copies take 0.18–0.20, 0.44–0.45 and 0.76–0.79 µs at the start, halfway (231 picks) and at
      the end (462 picks).
    - Every target is still met.
  - Fuzzing: 20,000 Games and 12,805,761 Decisions in 271 s (battery, power-saver), with no
    failures. The longest Game lasted 42 Generations.

**Code review** (`/code-review`, standards and spec):
- Fixed:
  - Glossary words:
    - a test name and comments said "choices" (an _Avoid_ word for Option); they now say what
      Players are dealt or buy;
    - "every other round" (an _Avoid_ word for Generation) became "seeds 4 to 7, 12 to 15 and so
      on".
  - Tests:
    - the hidden-information test covered only the setup buy. It now also covers a Research
      phase (3 Players), shared through `assert_no_player_view_shows_what_others_buy`;
    - the Research deal is now tested for 2–5 Players;
    - writing them turned up two traps: "research" is also a card id (Research, #090), and the log
      line "Research phase…" names that card;
    - `buy()` moved into `tests/helpers.py`, and a long lookup chain uses `buying()`.
  - The server leaked how many cards a Random Bot bought, through the time spent waiting on it.
    Random Bots now buy without pausing (`GameSession.waiting_on_random_bot_to_buy`), with a test.
  - "Fold" did nothing while a card in the hand could be played or sold. The dock now unfolds when
    a new such Decision arrives, and can be folded again.
  - Duplication:
    - `offer_buying_from` and `offer_final_greenery_from` share `first_in_player_order_who`;
    - the deal and the reveal share `player_order()`;
    - the GUI's three catalog lookups share `useCardsById`, and its "not implemented" note
      `notImplementedNote`;
    - "phase is setup or research" is `Phase::is_buying` and `playersAreBuying`.
  - The pair `dealt` and `bought` became the `Buying` type.
  - Names: `Deck::of` became `Deck::shuffled_from`.
  - `useFitZoom` read another component's CSS class; it now reads the page's
    `--hand-dock-height`.
  - Small things: a missing doc comment and docstring, a 125-column line, and the sale price
    read from the Option.
- Left as is:
  - Sell Patents is special-cased in `StandardProject` (price 0, its own `resolve` arm and an
    `unreachable!` in the shared one), because it is printed among the Standard Projects but
    gains MegaCredits instead.
  - The `Done` arms in `resolve` check the state (selling, final Greenery, otherwise buying), like
    `decision()`, as in ticket 04.
  - `CARD_PRICE` is copied into the GUI, like the other printed facts in `tracks.ts`.
  - Beyond the ticket text:
    - the dock unfolding by itself;
    - "Look at the board";
    - the "Not implemented" ribbons;
    - the fuzzer's setting.

    They serve play-testing.

**Open points:**
- **Hidden information through sequence numbers:** a Decision's `sequence` counts every pick, so a
  human who buys after a Random Bot could work out how many cards it bought. The GUI never shows
  it. Phase 2's encoding of the Player View for the AI must leave the sequence out.
- **Old Replay files** saved before this ticket no longer load. Their first picks now answer the
  setup buy.
- **Ticket 10 (Draft):**
  - the drafted cards become `Buying::dealt`;
  - `settings_for` gains a Draft setting;
  - ADR 0004's Game length should be checked again.
- **Ticket 23:**
  - with Sell Patents the status bar wraps to two lines at 1440 px. The Milestones and Awards bar
    then just reaches the dock at 1440×900; with one line it clears it;
  - at 1024×768 the bar is below the dock, as it was below the fold before;
  - the buying panel doesn't resize its cards when the dock is folded during buying.
- **Glossary:** "discard pile", "Research phase" and "Sell Patents" are used throughout but are
  not in CONTEXT.md. They are candidates for `/domain-modeling`.
- **Status line:** it stays `ready-for-agent`, because `docs/agents/triage-labels.md` has no
  "done" label.
