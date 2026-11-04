import { isYou, PLAYER_COLOURS } from "../players";
import type { Card, CardType, Decision, DecisionOption } from "../types";
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
 * spends or does, which card it buys, or which card it adds to or takes from; null otherwise. */
function actionUnderWay(game: GameUpdate): string | null {
  const { decision, view } = game;
  const details = decision?.options[0]?.details;
  if (decision?.kind === "payment" && details?.action) return details.card as string;
  if (decision?.kind === "resources" || decision?.kind === "effects") return details?.card as string;
  if (decision?.kind === "add_to_card" || details?.type === "move_card_resource") return details?.card as string;
  const keeping = decision?.kind === "keep_cards" ? view.players[decision.player].keeping : null;
  return keeping && keeping.price > 0 ? keeping.card : null;
}

/** The played card each Option is picked on, by its details: the card whose action it uses, or
 * the card that gets or loses Card Resources. Those two are status-bar buttons as well. */
const PICKED_ON_A_CARD: Record<string, string> = {
  use_action: "card",
  add_card_resources: "to",
  move_card_resource: "from",
};

/** The Options picked by clicking a played card, by the card's id. */
function cardOptions(decision: Decision | null): Map<string, DecisionOption> {
  const options = decision?.options.filter((option) => option.details.type in PICKED_ON_A_CARD) ?? [];
  return new Map(options.map((option) => [option.details[PICKED_ON_A_CARD[option.details.type]] as string, option]));
}

/** How the Card Resources on a card are written, for its tooltip: "1 microbe", "3 science". */
function cardResourcesText(kind: string, amount: number): string {
  return `${amount} ${kind}${amount === 1 || kind === "science" ? "" : "s"}`;
}

/** Under the board: each Player's played cards, grouped by type. They overlap so that each shows
 * its cost, title and Tags, and enlarge on hover. A card whose action can be used now, or that the
 * Decision offers to give or take Card Resources, is outlined and clicked to do so; one whose action
 * is used this Generation is dimmed and marked "Used". A card that holds Card Resources shows how
 * many are on it. (The hands are in the hand dock.) */
export function PlayedCards({ game, cards, disabled, onPick }: Props) {
  const catalog = useCardsById(cards);
  if (catalog.size === 0) return null;
  const card = (id: string) => catalog.get(id)!;
  const { decision } = game;
  const clickable = cardOptions(decision);
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
                        const option = clickable.get(each.id);
                        const used = board.used_actions.includes(each.id);
                        const onCard = board.card_resources[each.id];
                        const onCardText =
                          onCard === undefined ? "" : cardResourcesText(each.effects?.holds as string, onCard);
                        const badges = (used || onCard !== undefined) && (
                          <span className="card-badges">
                            {onCard !== undefined && (
                              <span className="card-resource-badge" title={onCardText}>
                                <span className="printed-card card-resource-icon">
                                  <span className={`resource ${each.effects?.holds as string}`} />
                                </span>
                                {onCard}
                              </span>
                            )}
                            {used && (
                              <span className="used-action-badge" aria-hidden>
                                Used
                              </span>
                            )}
                          </span>
                        );
                        const named = onCard === undefined ? each.name : `${each.name}, ${onCardText} on it`;
                        if (decision && option !== undefined) {
                          return (
                            <button
                              key={each.id}
                              className="small-card stacked playable"
                              disabled={disabled}
                              aria-label={onCard === undefined ? option.label : `${option.label}, ${onCardText} on it`}
                              onClick={() => onPick(decision.sequence, option.index)}
                            >
                              <PrintedCard card={each} />
                              {badges}
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
                            aria-label={used ? `${named} (action used this Generation)` : named}
                          >
                            <PrintedCard card={each} />
                            {badges}
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
