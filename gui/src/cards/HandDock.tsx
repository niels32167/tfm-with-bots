import { useState } from "react";

import { cardBeingPaidFor } from "../components/PaymentPicker";
import { isYou, PLAYER_COLOURS } from "../players";
import type { Card, Decision, DecisionOption } from "../types";
import type { GameUpdate } from "../useGameServer";
import { notImplementedNote, useCardsById } from "./catalog";
import { PrintedCard } from "./PrintedCard";

interface Props {
  game: GameUpdate;
  /** The card catalog. */
  cards: Card[];
  /** True while a pick is on its way to the server. */
  disabled: boolean;
  onPick: (sequence: number, index: number) => void;
  folded: boolean;
  onFold: (folded: boolean) => void;
}

/** The Options picked by clicking a card in the hand: playing it, or selling it with Sell
 * Patents, by the card's id. */
export function handOptions(decision: Decision | null): Map<string, DecisionOption> {
  const options = decision?.options.filter(
    (option) => option.details.type === "play_card" || option.details.type === "sell_card",
  );
  return new Map(options?.map((option) => [option.details.card as string, option]));
}

/** The hand, docked at the bottom of the window so it is always in reach. Only the tops of the
 * cards show (cost, Tags, title); hovering one lifts it into full view. Cards that can be played
 * or sold now are outlined and clicked to do so. In the full view (Hotseat, or only Random Bots)
 * a tab per Player picks whose hand to show, following the Player deciding. It folds away to a
 * single line. */
export function HandDock({ game, cards, disabled, onPick, folded, onFold }: Props) {
  const catalog = useCardsById(cards);
  // A hand picked by its tab, for as long as the same Player is deciding.
  const [picked, setPicked] = useState<{ player: number; whileDeciding: number | null } | null>(null);
  const { view, decision } = game;
  const deciding = decision?.player ?? view.current_player;
  const shown =
    game.viewer ?? (picked !== null && picked.whileDeciding === deciding ? picked.player : (deciding ?? 0));
  const hand = view.players[shown].hand ?? [];
  const options = handOptions(decision);
  const payingFor = cardBeingPaidFor(decision);
  const selling = decision?.kind === "sell_patents";

  return (
    <section className="hand-dock" aria-label="Hand" style={{ borderTopColor: PLAYER_COLOURS[shown] }}>
      <header className="hand-dock-header">
        {game.viewer === null ? (
          <div className="segmented hand-tabs" role="group" aria-label="Whose hand">
            {view.players.map((board, player) => (
              <button
                key={player}
                className={player === shown ? "selected" : ""}
                aria-pressed={player === shown}
                onClick={() => setPicked({ player, whileDeciding: deciding })}
              >
                <span className="player-dot" style={{ background: PLAYER_COLOURS[player] }} />
                {board.name}'s hand ({board.hand_size})
              </button>
            ))}
          </div>
        ) : (
          <h2>
            {isYou(game, shown) ? "Your hand" : `${view.players[shown].name}'s hand`} ({hand.length})
          </h2>
        )}
        {!folded && options.size > 0 && (
          <span className="hand-dock-hint">
            {selling ? "Click a card to sell it" : "Click a highlighted card to play it"}
          </span>
        )}
        <button className="link-button hand-dock-fold" onClick={() => onFold(!folded)}>
          {folded ? "Show the hand ▴" : "Fold ▾"}
        </button>
      </header>
      {!folded && (
        <div className="hand-dock-cards">
          {hand.map((id) => {
            const card = catalog.get(id);
            if (!card) return null;
            const option = options.get(id);
            if (decision && option) {
              const sell = option.details.type === "sell_card";
              return (
                <div key={id} className="hand-slot">
                  <button
                    className={`small-card in-dock ${sell ? "sellable" : "playable"}`}
                    disabled={disabled}
                    aria-label={`${sell ? "Sell" : "Play"} ${card.name}`}
                    onClick={() => onPick(decision.sequence, option.index)}
                  >
                    <PrintedCard card={card} />
                  </button>
                </div>
              );
            }
            const note = notImplementedNote(card);
            const state = id === payingFor ? "being-paid-for" : note && !selling ? "not-implemented" : "";
            return (
              <div key={id} className="hand-slot">
                <div className={`small-card in-dock ${state}`} tabIndex={0} aria-label={card.name} title={note}>
                  <PrintedCard card={card} />
                </div>
              </div>
            );
          })}
          {hand.length === 0 && <p className="no-cards">No cards in hand.</p>}
        </div>
      )}
    </section>
  );
}
