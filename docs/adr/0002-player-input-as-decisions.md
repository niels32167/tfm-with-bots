# Every player choice is a Decision with a finite list of Options

The engine is always waiting on exactly one Decision for one Player, and it moves forward only when one of that Decision's Options is picked. A compound Action (play a card, pay for it, place a Tile, pick a target) becomes a chain of small Decisions rather than one combined action, because listing every combination of payment, placement and target explodes in size.

Steps that happen at the same time at a real table, like buying research cards and drafting, are taken one Player at a time in player order. Nobody can tell, since those choices are hidden.

The GUI, the Random Bot and the future AI all answer Decisions the same way, so any Controller can take over any Player without new plumbing.
