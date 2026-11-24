# What only a human needs is asked at the screen, not by the engine

A human wants to try out cards before choosing, to press a button before cards are drawn, to end their Turn themselves,
to take back a misclick without peeking, and to see what a bot would do. A bot wants none of it. So the server and the
GUI do these around the engine's Decisions, which stay as they are (ADR 0002):

- **Choosing cards.** The GUI toggles cards and sends those chosen at once. `server/card_choice.py` answers the Decisions
  they belong to, all or none: at setup the Corporation, the Prelude Cards and the Project Cards bought together.
- **Drawing.** A pick that would take cards from a deck is answered with what it draws, and made only once confirmed
  (`server/drawing.py` tries it on a copy of the Game). The message says only what the rules already tell.
  A choice of cards has its own button, such as "Play Research Network", and isn't asked for twice.
- **End Turn.** After a human's second Action, or their last Prelude Card, the registered Controllers wait for End Turn.
- **Undo.** Against registered Controllers it goes back through the human's own picks until another Player picks, a card
  leaves a deck, Draft hands are passed on, the Generation ends, or a phase everyone chooses in secretly ends. The last Player's Prelude Cards may
  be undone into Generation 1. With two or more humans (Hotseat) or none the screen shows everything anyway, so undo
  stays unlimited there, also for finding bugs.
- **Advice.** A registered Controller is asked what it would do through the handle of the human's Player (ADR 0013), so
  it knows no more than they do. The server follows its choice of cards on a copy of the Game only until its
  Player would be done, and looks at nothing beyond.

**The one exception in the engine** is the setting `ask_last_prelude_card`: the last Prelude Card, played at once
otherwise, is then a Decision with one Option. The position between the two Prelude Cards exists nowhere else. The
server sets it for a Game with a human. It is off unless named, so old Replays, Matches, training and the benchmark play
as before, and bots that look ahead pick it as a follow-up.

**Considered option:** *Decisions with one Option in the engine for every draw and at the end of every Turn.* They
would stretch every Replay, change the positions the models were trained on, slow self-play down and break old Replays,
for something only a person at a screen notices.

**What this gives up:** saving a Replay and loading it again still gets around undo, as Save and Load Replay are tools
for testing. And the confirmation comes before the whole pick, so a Tile that draws a card is put down only once the draw
is confirmed.
