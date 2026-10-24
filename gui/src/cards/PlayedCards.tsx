import { isYou, PLAYER_COLOURS } from "../players";
import type { Card, CardType } from "../types";
import type { GameUpdate } from "../useGameServer";
import { useCardsById } from "./catalog";
import { PrintedCard } from "./PrintedCard";

interface Props {
  game: GameUpdate;
  /** The card catalog. */
  cards: Card[];
}

// Played cards are grouped by type, as on Board Game Arena.
const PLAYED_GROUPS: { type: CardType; label: string }[] = [
  { type: "automated", label: "Automated" },
  { type: "active", label: "Active" },
  { type: "event", label: "Events" },
];

/** Under the board: each Player's played cards, grouped by type. They overlap so that each shows
 * its cost, title and Tags, and enlarge on hover. (The hands are in the hand dock.) */
export function PlayedCards({ game, cards }: Props) {
  const catalog = useCardsById(cards);
  if (catalog.size === 0) return null;
  const card = (id: string) => catalog.get(id)!;

  return (
    <section className="player-cards" aria-label="Played cards">
      {game.view.players.map((board, player) => (
        <div key={player} className="card-row played" style={{ borderLeftColor: PLAYER_COLOURS[player] }}>
          <h3>
            {isYou(game, player) ? "Your" : `${board.name}'s`} played cards ({board.played_cards.length})
          </h3>
          <div className="played-groups">
            {PLAYED_GROUPS.map(({ type, label }) => {
              const group = board.played_cards.map(card).filter((each) => each.type === type);
              return (
                group.length > 0 && (
                  <div key={type} className="played-group">
                    <h4>
                      {label} ({group.length})
                    </h4>
                    <div className="card-stack">
                      {group.map((each) => (
                        <div key={each.id} className="small-card stacked" tabIndex={0} aria-label={each.name}>
                          <PrintedCard card={each} />
                        </div>
                      ))}
                    </div>
                  </div>
                )
              );
            })}
            {board.played_cards.length === 0 && <p className="no-cards">No cards played yet.</p>}
          </div>
        </div>
      ))}
    </section>
  );
}
