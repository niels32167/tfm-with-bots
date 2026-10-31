import { isYou, PLAYER_COLOURS } from "../players";
import type { Card, CardType, Decision } from "../types";
import type { GameUpdate } from "../useGameServer";
import { useCardsById } from "./catalog";
import { PrintedCard } from "./PrintedCard";

interface Props {
  game: GameUpdate;
  /** The card catalog. */
  cards: Card[];
  /** True while a pick is on its way to the server. */
  disabled: boolean;
  onPick: (sequence: number, index: number) => void;
}

// Played cards are grouped by type, as on Board Game Arena.
const PLAYED_GROUPS: { type: CardType; label: string }[] = [
  { type: "automated", label: "Automated" },
  { type: "active", label: "Active" },
  { type: "event", label: "Events" },
];

/** The card whose action is being carried out while the Game waits on how to pay for it, what it
 * spends, or which card it buys; null otherwise. */
function actionUnderWay(game: GameUpdate): string | null {
  const { decision, view } = game;
  const details = decision?.options[0]?.details;
  if (decision?.kind === "payment" && details?.action) return details.card as string;
  if (decision?.kind === "resources") return details?.card as string;
  const keeping = decision?.kind === "keep_cards" ? view.players[decision.player].keeping : null;
  return keeping && keeping.price > 0 ? keeping.card : null;
}

/** The Options that use a played card's action, by the card's id. */
function actionOptions(decision: Decision | null): Map<string, number> {
  const options = decision?.options.filter((option) => option.details.type === "use_action") ?? [];
  return new Map(options.map((option) => [option.details.card as string, option.index]));
}

/** Under the board: each Player's played cards, grouped by type. They overlap so that each shows
 * its cost, title and Tags, and enlarge on hover. A card whose action can be used now is
 * outlined and clicked to use it; one whose action is used this Generation is dimmed and marked
 * "Used". (The hands are in the hand dock.) */
export function PlayedCards({ game, cards, disabled, onPick }: Props) {
  const catalog = useCardsById(cards);
  if (catalog.size === 0) return null;
  const card = (id: string) => catalog.get(id)!;
  const { decision } = game;
  const usable = actionOptions(decision);
  const underWay = actionUnderWay(game);

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
                      {group.map((each) => {
                        const option = decision?.player === player ? usable.get(each.id) : undefined;
                        const used = board.used_actions.includes(each.id);
                        const badge = used && (
                          <span className="used-action-badge" aria-hidden>
                            Used
                          </span>
                        );
                        if (decision && option !== undefined) {
                          return (
                            <button
                              key={each.id}
                              className="small-card stacked playable"
                              disabled={disabled}
                              aria-label={`Use the action of ${each.name}`}
                              onClick={() => onPick(decision.sequence, option)}
                            >
                              <PrintedCard card={each} />
                            </button>
                          );
                        }
                        // The card whose action is under way is outlined rather than dimmed.
                        const state = each.id === underWay ? "action-under-way" : used ? "used-action" : "";
                        return (
                          <div
                            key={each.id}
                            className={`small-card stacked ${state}`}
                            tabIndex={0}
                            aria-label={used ? `${each.name} (action used this Generation)` : each.name}
                          >
                            <PrintedCard card={each} />
                            {badge}
                          </div>
                        );
                      })}
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
