import { useEffect, useRef, useState } from "react";

import { isYou, playerTitle } from "../players";
import type { Card, Decision, PlayerBoard, View } from "../types";
import type { GameUpdate } from "../useGameServer";
import { notImplementedNote, useCardsById } from "./catalog";
import { PrintedCard } from "./PrintedCard";
import { useFitZoom } from "./useFitZoom";

/** What buying a dealt card costs, in MegaCredits. */
export const CARD_PRICE = 3;

/** How many of the Prelude Cards dealt at setup each Player keeps. */
const PRELUDE_CARDS_KEPT = 2;

// Pixels between the cards.
const GAP = 14;

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

/** Whose cards the buying panel shows: the human deciding while Players draft or buy, keep cards they
 * look at, or keep or play Prelude Cards, or else the one human at the screen. Null when there is
 * nothing to show. */
export function cardsShownFor(game: GameUpdate): number | null {
  const { decision, viewer, view } = game;
  const pickingCards = ["corporation", "prelude_cards", "draft", "buy_cards", "keep_cards", "play_prelude_card"];
  if (decision && pickingCards.includes(decision.kind)) return decision.player;
  if (viewer === null) return null;
  const { drafting, buying, keeping, prelude_cards } = view.players[viewer];
  const preludeCardsToPlay = view.phase === "prelude_cards" && (prelude_cards?.kept.length ?? 0) > 0;
  return drafting || buying || keeping || preludeCardsToPlay ? viewer : null;
}

/** Whether `board`'s Player, at setup, still keeps Prelude Cards: they were dealt some and kept fewer than 2. */
function keepingPreludeCards(view: View, board: PlayerBoard): boolean {
  const cards = board.prelude_cards;
  return view.phase === "setup" && cards !== null && cards.dealt.length > 0 && cards.kept.length < PRELUDE_CARDS_KEPT;
}

/** The Option of `type` for each card, by the card's id, while `player` decides. */
function optionsByCard(decision: Decision | null, player: number, type: string): Map<string, number> {
  if (decision?.player !== player) return new Map();
  const options = decision.options.filter((option) => option.details.type === type);
  return new Map(options.map((option) => [option.details.card as string, option.index]));
}

/** Over the board in the setup and each Research phase: the Corporations a Player chooses from and
 * the cards they draft from or buy from, large enough to read and all in view. Choosing a Corporation,
 * the Project Cards dealt show above; in the Draft, clicking one keeps it, and the cards kept and
 * passed on so far show above; buying, clicking one buys it, those bought are marked, the
 * Corporation they chose shows above, and Done is in the status bar. The cards a card such as Business
 * Contacts lets its Player look at show the same way as the Draft's. It can be hidden to look at the
 * board. */
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
  const choosing = board.choosing_corporation;
  const preludeCards = board.prelude_cards;
  const panel = board.keeping
    ? keepingPanel(game, shown, catalog)
    : board.drafting
      ? draftPanel(game, shown)
      : choosing && choosing.picked === null
        ? corporationPanel(game, shown)
        : keepingPreludeCards(view, board)
          ? preludeKeepingPanel(game, shown)
          : board.buying
            ? buyingPanel(game, shown)
            : playingPreludeCards(game, shown)
              ? preludePlayingPanel(game, shown)
              : null;
  const kept = board.keeping?.kept ?? board.drafting?.kept;
  // At setup, the Prelude Cards kept show above the cards to buy, as the Corporation chosen does.
  const preludeCardsKept = view.phase === "setup" && !keepingPreludeCards(view, board) ? preludeCards?.kept : undefined;
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
      {!hidden && (kept || passedThisGeneration.length > 0 || choosing || preludeCardsKept) && (
        <div className="buying-panel-strip">
          {choosing?.picked && <SmallCards label="Corporation, hidden for now" groups={[named([choosing.picked])]} />}
          {preludeCardsKept && preludeCardsKept.length > 0 && (
            <SmallCards label="Prelude Cards kept, hidden for now" groups={[named(preludeCardsKept)]} />
          )}
          {choosing?.picked === null && preludeCards && preludeCards.dealt.length > 0 && (
            <SmallCards label="Prelude Cards to keep from next" groups={[named(preludeCards.dealt)]} />
          )}
          {choosing?.picked === null && board.buying && (
            <SmallCards label="Project Cards to buy from next" groups={[named(board.buying.dealt)]} />
          )}
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
          marked={panel.marked ?? board.buying?.bought ?? []}
          markedAs={panel.markedAs ?? "Bought"}
          notes={panel.notes ?? new Map()}
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
  /** The cards marked as picked already, and what the mark says: the cards bought, unless given. */
  marked?: string[];
  markedAs?: string;
  /** A ribbon on some of the cards, by id. */
  notes?: Map<string, string>;
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

/** At setup, while `player` has not chosen: the Corporations dealt to them. */
function corporationPanel(game: GameUpdate, player: number): Panel {
  const { dealt } = game.view.players[player].choosing_corporation!;
  return {
    label: "Corporations to choose from",
    heading: `Setup: ${whose(game, player)} Corporations`,
    summary: "Choose one · it stays hidden until every Player is done buying",
    waitingFor: "choose a Corporation",
    cards: dealt,
    optionType: "choose_corporation",
    verb: "Choose",
  };
}

/** At setup, once `player` has chosen their Corporation: the Prelude Cards dealt to them, to keep 2 of. */
function preludeKeepingPanel(game: GameUpdate, player: number): Panel {
  const { dealt, kept } = game.view.players[player].prelude_cards!;
  return {
    label: "Prelude Cards to keep",
    heading: `Setup: ${whose(game, player)} ${dealt.length} Prelude Cards`,
    summary: `Keep ${PRELUDE_CARDS_KEPT} · they stay hidden until played · ${kept.length} kept`,
    waitingFor: "keep Prelude Cards",
    cards: dealt,
    optionType: "keep_prelude_card",
    verb: "Keep",
    marked: kept,
    markedAs: "Kept",
  };
}

/** Whether `player` has Prelude Cards to play now: after setup, or those drawn for a first action. */
function playingPreludeCards(game: GameUpdate, player: number): boolean {
  const toPlay = game.view.players[player].prelude_cards?.kept.length ?? 0;
  return (game.view.phase === "prelude_cards" || drawnForAFirstAction(game, player)) && toPlay > 0;
}

/** Whether `player` is choosing which of the Prelude Cards they drew to play, as their Corporation's first
 * action (Valley Trust), in the Action phase. */
function drawnForAFirstAction(game: GameUpdate, player: number): boolean {
  const { decision, view } = game;
  return view.phase === "action" && decision?.kind === "play_prelude_card" && decision.player === player;
}

/** After setup: the Prelude Cards `player` kept and has still to play, the one picked first. One that
 * can't be played is marked: picking it discards it for 15 MegaCredits. As Valley Trust's first action:
 * the Prelude Cards they drew, one of them to play. */
function preludePlayingPanel(game: GameUpdate, player: number): Panel {
  const { kept } = game.view.players[player].prelude_cards!;
  const { decision } = game;
  const unplayable = (decision?.player === player ? decision.options : []).filter(
    (option) => option.details.type === "play_prelude_card" && option.details.playable === false,
  );
  const drawn = drawnForAFirstAction(game, player);
  return {
    label: "Prelude Cards to play",
    heading: drawn
      ? `First action: ${whose(game, player)} ${kept.length} Prelude Card${kept.length === 1 ? "" : "s"} drawn`
      : `Before Generation 1: ${whose(game, player)} Prelude Cards`,
    summary: drawn
      ? "Play one · the others are discarded, unseen by the other Players"
      : kept.length > 1
        ? "Play both, one at a time · click the one to play first"
        : "The last one is played next",
    waitingFor: "play Prelude Cards",
    cards: kept,
    optionType: "play_prelude_card",
    verb: "Play",
    notes: new Map(unplayable.map((option) => [option.details.card as string, "Can't be played: discard for 15 MegaCredits"])),
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
  const { dealt, bought, megacredits } = game.view.players[player].buying!;
  return {
    label: "Cards to buy",
    heading:
      game.view.phase === "setup"
        ? `Setup: ${whose(game, player)} ${dealt.length} Project Cards`
        : `Research phase: ${whose(game, player)} ${dealt.length} cards`,
    summary: `${bought.length} bought, ${bought.length * CARD_PRICE} of ${megacredits} MegaCredits · ${CARD_PRICE} each`,
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

/** A labelled row of small cards; pointing at one enlarges it to read (`CardZoom`). */
function SmallCards({ label, groups }: SmallCardsProps) {
  return (
    <div className="buying-panel-small-cards">
      <h3>{label}</h3>
      {groups.map((group, index) => (
        <div key={index} className="small-card-group">
          {group.map((card) => (
            <div key={card.id} className="small-card in-strip" tabIndex={0} aria-label={card.name} data-zoom-card={card.id}>
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
  /** The ids of the cards picked so far, bought or kept, and the ribbon on them. */
  marked: string[];
  markedAs: string;
  /** A ribbon on some of the cards, by id. */
  notes: Map<string, string>;
  /** The Option that picks each card, by its id, while the Player shown decides. */
  options: Map<string, number>;
  /** What picking a card does: "Buy" or "Keep". */
  verb: string;
  disabled: boolean;
  onPick: (index: number) => void;
}

/** The cards to pick from, as large as the space in view allows. */
function PanelCards({ cards, marked, markedAs, notes, options, verb, disabled, onPick }: PanelCardsProps) {
  const cardsRef = useRef<HTMLDivElement>(null);
  const zoom = useFitZoom(cardsRef, cards.length, GAP);
  const style = { zoom };
  return (
    <div ref={cardsRef} className="buying-panel-cards" style={{ gap: GAP }}>
      {cards.map((card) => {
        const optionIndex = options.get(card.id);
        const isMarked = marked.includes(card.id);
        const note = notImplementedNote(card);
        const ribbon = notes.get(card.id);
        const face = (
          <>
            <PrintedCard card={card} />
            {isMarked && <span className="card-ribbon bought">{markedAs}</span>}
            {note && <span className="card-ribbon not-implemented">Not implemented</span>}
            {ribbon && <span className="card-ribbon not-implemented">{ribbon}</span>}
          </>
        );
        if (optionIndex !== undefined) {
          return (
            <button
              key={card.id}
              className="buy-card buyable"
              style={style}
              disabled={disabled}
              title={ribbon ?? note}
              aria-label={`${verb} ${card.name}${ribbon ? `: ${ribbon}` : ""}`}
              onClick={() => onPick(optionIndex)}
              data-zoom-card={card.id}
            >
              {face}
            </button>
          );
        }
        return (
          <div
            key={card.id}
            className={`buy-card ${isMarked ? "bought" : ""}`}
            style={style}
            tabIndex={0}
            aria-label={card.name}
            title={note}
            data-zoom-card={card.id}
          >
            {face}
          </div>
        );
      })}
    </div>
  );
}
