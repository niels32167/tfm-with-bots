import { useMemo } from "react";

import { cardBeingPaidFor } from "../components/PaymentPicker";
import { isYou, PLAYER_COLOURS } from "../players";
import type { Card, CardType } from "../types";
import type { GameUpdate } from "../useGameServer";
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

/** Under the board: the hands the view shows (the viewer's own, or every hand in the full
 * view) and each Player's played cards. A card that can be played now is outlined in its
 * hand, and clicking it plays it; the card being paid for is marked too. Cards are drawn
 * small and enlarge on hover. */
export function PlayerCards({ game, cards, disabled, onPick }: Props) {
  const catalog = useMemo(() => new Map(cards.map((card) => [card.id, card])), [cards]);
  if (catalog.size === 0) return null;
  const { view, decision } = game;
  const card = (id: string) => catalog.get(id)!;
  // The Option that plays each card, by the card's id.
  const playOptions = new Map(
    decision?.options
      .filter((option) => option.details.type === "play_card")
      .map((option) => [option.details.card as string, option.index]),
  );
  const payingFor = cardBeingPaidFor(decision);

  return (
    <section className="player-cards" aria-label="Cards">
      {view.players.map(
        (board, player) =>
          board.hand !== null && (
            <div key={`hand-${player}`} className="card-row hand" style={{ borderLeftColor: PLAYER_COLOURS[player] }}>
              <h3>
                {isYou(game, player) ? "Your hand" : `${board.name}'s hand`} ({board.hand_size})
              </h3>
              <div className="hand-cards">
                {board.hand.map((id) => {
                  const optionIndex = playOptions.get(id);
                  if (decision && optionIndex !== undefined) {
                    return (
                      <button
                        key={id}
                        className="small-card in-hand playable"
                        disabled={disabled}
                        aria-label={`Play ${card(id).name}`}
                        onClick={() => onPick(decision.sequence, optionIndex)}
                      >
                        <PrintedCard card={card(id)} />
                      </button>
                    );
                  }
                  const implemented = card(id).effects !== undefined;
                  const state = id === payingFor ? "being-paid-for" : implemented ? "" : "not-implemented";
                  return (
                    <div
                      key={id}
                      className={`small-card in-hand ${state}`}
                      title={implemented ? undefined : "Not implemented yet, so it can't be played"}
                    >
                      <PrintedCard card={card(id)} />
                    </div>
                  );
                })}
                {board.hand.length === 0 && <p className="no-cards">No cards in hand.</p>}
              </div>
            </div>
          ),
      )}
      {view.players.map((board, player) => (
        <div key={`played-${player}`} className="card-row played" style={{ borderLeftColor: PLAYER_COLOURS[player] }}>
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
