import { type CSSProperties, useEffect, useRef, useState } from "react";

import { isYou, playerTitle } from "../players";
import type { Card, Decision, View } from "../types";
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

/** Whose cards the buying panel shows: the human deciding while Players draft or buy, or keep
 * cards they look at, or else the one human at the screen. Null when there is nothing to show. */
export function cardsShownFor(game: GameUpdate): number | null {
  const { decision, viewer, view } = game;
  if (decision?.kind === "draft" || decision?.kind === "buy_cards" || decision?.kind === "keep_cards") {
    return decision.player;
  }
  if (viewer === null) return null;
  const { drafting, buying, keeping } = view.players[viewer];
  return drafting || buying || keeping ? viewer : null;
}

/** The Option of `type` for each card, by the card's id, while `player` decides. */
function optionsByCard(decision: Decision | null, player: number, type: string): Map<string, number> {
  if (decision?.player !== player) return new Map();
  const options = decision.options.filter((option) => option.details.type === type);
  return new Map(options.map((option) => [option.details.card as string, option.index]));
}

/** Over the board in the setup and each Research phase: the cards a Player drafts from or buys
 * from, large enough to read and all in view. In the Draft, clicking one keeps it, and the cards
 * kept and passed on so far show above; buying, clicking one buys it, those bought are marked,
 * and Done is in the status bar. The cards a card such as Business Contacts lets its Player look
 * at show the same way as the Draft's. It can be hidden to look at the board. */
export function BuyingPanel({ game, cards, disabled, onPick }: Props) {
  const catalog = useCardsById(cards);
  const [hidden, setHidden] = useState(false);
  // The panel opens at the top of the page, so the cards are in view without scrolling.
  useEffect(() => {
    window.scrollTo({ top: 0 });
  }, []);
  const shown = cardsShownFor(game);
  if (shown === null || catalog.size === 0) return null;
  const { view, decision } = game;
  const board = view.players[shown];
  const panel = board.keeping
    ? keepingPanel(game, shown, catalog)
    : board.drafting
      ? draftPanel(game, shown)
      : board.buying
        ? buyingPanel(game, shown)
        : null;
  const kept = board.keeping?.kept ?? board.drafting?.kept;
  if (panel === null) return null;
  const waitingFor = view.current_player !== null && view.current_player !== shown ? view.current_player : null;
  const passedThisGeneration = (board.passed_in_draft ?? []).filter((pass) => pass.generation === view.generation);
  const named = (ids: string[]) => ids.map((id) => catalog.get(id)!);

  return (
    <section className={`buying-panel ${hidden ? "hidden" : ""}`} aria-label={panel.label}>
      <header className="buying-panel-header">
        <h2>{panel.heading}</h2>
        <span className="buying-panel-total">{panel.summary}</span>
        {waitingFor !== null && (
          <span className="buying-panel-waiting">
            Waiting for {playerTitle(game, waitingFor)} to {panel.waitingFor}…
          </span>
        )}
        <button className="link-button" onClick={() => setHidden(!hidden)}>
          {hidden ? "Show the cards" : "Look at the board"}
        </button>
      </header>
      {!hidden && (kept || passedThisGeneration.length > 0) && (
        <div className="buying-panel-strip">
          {kept && (
            <SmallCards label={`${board.keeping?.price ? "Bought" : "Kept"} (${kept.length})`} groups={[named(kept)]} />
          )}
          {!board.keeping && passedThisGeneration.length > 0 && (
            <SmallCards
              label={`Passed to ${playerTitle(game, passedThisGeneration[0].to)}`}
              groups={passedThisGeneration.map((pass) => named(pass.cards))}
            />
          )}
        </div>
      )}
      {!hidden && (
        <PanelCards
          cards={named(panel.cards)}
          bought={board.buying?.bought ?? []}
          options={optionsByCard(decision, shown, panel.optionType)}
          verb={panel.verb}
          disabled={disabled}
          onPick={(index) => decision && onPick(decision.sequence, index)}
        />
      )}
    </section>
  );
}

/** What the panel shows and says for one Player's cards. */
interface Panel {
  label: string;
  heading: string;
  summary: string;
  /** What the Player waited for is doing: "keep a card". */
  waitingFor: string;
  /** The ids of the cards shown large, to pick from. */
  cards: string[];
  /** The type of the Options that pick them, and the verb on their buttons. */
  optionType: string;
  verb: string;
}

/** "your", or "Player 2's". */
function whose(game: GameUpdate, player: number): string {
  return isYou(game, player) ? "your" : `${game.view.players[player].name}'s`;
}

/** In the Draft: the cards `player` keeps one from now, passing the rest on. */
function draftPanel(game: GameUpdate, player: number): Panel {
  const { picking_from, kept, passing_to } = game.view.players[player].drafting!;
  return {
    label: "Cards to draft",
    heading: `Draft: ${whose(game, player)} ${picking_from.length} ${picking_from.length === 1 ? "card" : "cards"}`,
    summary: `Keep one and pass the rest to ${playerTitle(game, passing_to)} · ${kept.length} kept`,
    waitingFor: "keep a card",
    cards: picking_from,
    optionType: "draft_card",
    verb: "Keep",
  };
}

/** While `player` plays a card such as Business Contacts: the cards they look at and may still
 * keep, discarding the rest. Using the action of one such as Inventors' Guild, they may buy them
 * instead. */
function keepingPanel(game: GameUpdate, player: number, catalog: Map<string, Card>): Panel {
  const { card, looking_at, kept, keep, price } = game.view.players[player].keeping!;
  const name = catalog.get(card)?.name ?? card;
  const looked = looking_at.length + kept.length;
  if (price > 0) {
    return {
      label: "Cards to buy",
      heading: `${name}: ${whose(game, player)} top ${looked === 1 ? "card" : `${looked} cards`} from the deck`,
      summary: `Buy up to ${keep} for ${price} MegaCredits each, or Done to discard · ${kept.length} bought`,
      waitingFor: "buy or discard",
      cards: looking_at,
      optionType: "buy_card",
      verb: "Buy",
    };
  }
  return {
    label: "Cards to keep",
    heading: `${name}: ${whose(game, player)} top ${looked} cards from the deck`,
    summary: `Keep ${keep} more and discard the rest · ${kept.length} kept`,
    waitingFor: "keep cards",
    cards: looking_at,
    optionType: "keep_card",
    verb: "Keep",
  };
}

/** At setup and in a Research phase: the cards dealt to `player` (or kept in the Draft) to buy from. */
function buyingPanel(game: GameUpdate, player: number): Panel {
  const { dealt, bought } = game.view.players[player].buying!;
  return {
    label: "Cards to buy",
    heading:
      game.view.phase === "setup"
        ? `Setup: ${whose(game, player)} ${dealt.length} Project Cards`
        : `Research phase: ${whose(game, player)} ${dealt.length} cards`,
    summary: `${bought.length} bought, ${bought.length * CARD_PRICE} MegaCredits · ${CARD_PRICE} each`,
    waitingFor: "buy",
    cards: dealt,
    optionType: "buy_card",
    verb: "Buy",
  };
}

interface SmallCardsProps {
  label: string;
  /** The cards, in groups shown apart: each set passed on, say. */
  groups: Card[][];
}

/** A labelled row of small cards; hovering one enlarges it to read. */
function SmallCards({ label, groups }: SmallCardsProps) {
  return (
    <div className="buying-panel-small-cards">
      <h3>{label}</h3>
      {groups.map((group, index) => (
        <div key={index} className="small-card-group">
          {group.map((card) => (
            <div key={card.id} className="small-card in-strip" tabIndex={0} aria-label={card.name}>
              <PrintedCard card={card} />
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}

interface PanelCardsProps {
  cards: Card[];
  /** The ids of the cards bought so far. */
  bought: string[];
  /** The Option that picks each card, by its id, while the Player shown decides. */
  options: Map<string, number>;
  /** What picking a card does: "Buy" or "Keep". */
  verb: string;
  disabled: boolean;
  onPick: (index: number) => void;
}

/** The cards to pick from, as large as the space in view allows. */
function PanelCards({ cards, bought, options, verb, disabled, onPick }: PanelCardsProps) {
  const cardsRef = useRef<HTMLDivElement>(null);
  const zoom = useFitZoom(cardsRef, cards.length, GAP);
  const style = { zoom, "--hover-scale": Math.max(1.05, HOVER_ZOOM / zoom) } as CSSProperties;
  return (
    <div ref={cardsRef} className="buying-panel-cards" style={{ gap: GAP }}>
      {cards.map((card) => {
        const optionIndex = options.get(card.id);
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
              aria-label={`${verb} ${card.name}`}
              onClick={() => onPick(optionIndex)}
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
