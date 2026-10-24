import { type CSSProperties, useEffect, useRef, useState } from "react";

import { isYou, playerTitle } from "../players";
import type { Card, View } from "../types";
import type { GameUpdate } from "../useGameServer";
import { notImplementedNote, useCardsById } from "./catalog";
import { PrintedCard } from "./PrintedCard";
import { useFitZoom } from "./useFitZoom";

/** What buying a dealt card costs, in MegaCredits. */
export const CARD_PRICE = 3;

// Pixels between the cards.
const GAP = 14;
// Hovering a card enlarges it to about this zoom, so a small one becomes readable.
const HOVER_ZOOM = 0.85;

interface Props {
  game: GameUpdate;
  /** The card catalog. */
  cards: Card[];
  /** True while a pick is on its way to the server. */
  disabled: boolean;
  onPick: (sequence: number, index: number) => void;
}

/** Whether Players are buying cards: in the setup or a Research phase. */
export function playersAreBuying(view: View): boolean {
  return view.phase === "setup" || view.phase === "research";
}

/** Whose cards to buy from the buying panel shows: the human deciding, or else the one human at
 * the screen while Players buy. Null when there is nothing to show. */
export function buyerShown(game: GameUpdate): number | null {
  if (game.decision?.kind === "buy_cards") return game.decision.player;
  if (game.viewer !== null && game.view.players[game.viewer].buying) return game.viewer;
  return null;
}

/** Over the board in the setup and each Research phase: the cards dealt to a Player, large enough
 * to read and all in view. Clicking one buys it; those bought are marked, and Done is in the status
 * bar. It can be hidden to look at the board. */
export function BuyingPanel({ game, cards, disabled, onPick }: Props) {
  const catalog = useCardsById(cards);
  const [hidden, setHidden] = useState(false);
  // The panel opens at the top of the page, so the cards are in view without scrolling.
  useEffect(() => {
    window.scrollTo({ top: 0 });
  }, []);
  const buyer = buyerShown(game);
  const buying = buyer === null ? null : game.view.players[buyer].buying;
  if (buyer === null || buying === null || catalog.size === 0) return null;

  const { view, decision } = game;
  // The Option that buys each card, by the card's id, while this Player decides.
  const buyOptions = new Map(
    decision?.player === buyer
      ? decision.options
          .filter((option) => option.details.type === "buy_card")
          .map((option) => [option.details.card as string, option.index])
      : [],
  );
  const whose = isYou(game, buyer) ? "your" : `${view.players[buyer].name}'s`;
  const what =
    view.phase === "setup"
      ? `Setup: ${whose} ${buying.dealt.length} Project Cards`
      : `Research phase: ${whose} ${buying.dealt.length} cards`;
  const waitingFor = view.current_player !== null && view.current_player !== buyer ? view.current_player : null;

  return (
    <section className={`buying-panel ${hidden ? "hidden" : ""}`} aria-label="Cards to buy">
      <header className="buying-panel-header">
        <h2>{what}</h2>
        <span className="buying-panel-total">
          {buying.bought.length} bought, {buying.bought.length * CARD_PRICE} MegaCredits · {CARD_PRICE} each
        </span>
        {waitingFor !== null && (
          <span className="buying-panel-waiting">Waiting for {playerTitle(game, waitingFor)} to buy…</span>
        )}
        <button className="link-button" onClick={() => setHidden(!hidden)}>
          {hidden ? "Show the cards" : "Look at the board"}
        </button>
      </header>
      {!hidden && (
        <DealtCards
          dealt={buying.dealt.map((id) => catalog.get(id)!)}
          bought={buying.bought}
          buyOptions={buyOptions}
          disabled={disabled}
          onBuy={(index) => decision && onPick(decision.sequence, index)}
        />
      )}
    </section>
  );
}

interface DealtCardsProps {
  dealt: Card[];
  /** The ids of the cards bought so far. */
  bought: string[];
  /** The Option that buys each card, by its id, while the Player shown decides. */
  buyOptions: Map<string, number>;
  disabled: boolean;
  onBuy: (index: number) => void;
}

/** The cards dealt, as large as the space in view allows. */
function DealtCards({ dealt, bought, buyOptions, disabled, onBuy }: DealtCardsProps) {
  const cardsRef = useRef<HTMLDivElement>(null);
  const zoom = useFitZoom(cardsRef, dealt.length, GAP);
  const style = { zoom, "--hover-scale": Math.max(1.05, HOVER_ZOOM / zoom) } as CSSProperties;
  return (
    <div ref={cardsRef} className="buying-panel-cards" style={{ gap: GAP }}>
      {dealt.map((card) => {
        const optionIndex = buyOptions.get(card.id);
        const isBought = bought.includes(card.id);
        const note = notImplementedNote(card);
        const face = (
          <>
            <PrintedCard card={card} />
            {isBought && <span className="card-ribbon bought">Bought</span>}
            {note && <span className="card-ribbon not-implemented">Not implemented</span>}
          </>
        );
        if (optionIndex !== undefined) {
          return (
            <button
              key={card.id}
              className="buy-card buyable"
              style={style}
              disabled={disabled}
              title={note}
              aria-label={`Buy ${card.name}`}
              onClick={() => onBuy(optionIndex)}
            >
              {face}
            </button>
          );
        }
        return (
          <div
            key={card.id}
            className={`buy-card ${isBought ? "bought" : ""}`}
            style={style}
            tabIndex={0}
            aria-label={card.name}
            title={note}
          >
            {face}
          </div>
        );
      })}
    </div>
  );
}
