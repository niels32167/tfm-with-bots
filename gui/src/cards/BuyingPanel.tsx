import { useEffect, useRef, useState } from "react";

import { isYou, playerTitle } from "../players";
import type { Card, View } from "../types";
import type { GameUpdate } from "../useGameServer";
import { notImplementedNote, useCardsById } from "./catalog";
import { CARD_PRICE, type ChoiceState, PRELUDE_CARDS_KEPT, type Selection, startingMegaCredits } from "./choosing";
import { PrintedCard } from "./PrintedCard";
import { useFitZoom, useRowZoom } from "./useFitZoom";

// Pixels between the cards.
const GAP = 14;
// Pixels between the cards at setup, where three rows of them show at once.
const SETUP_GAP = 8;

interface Props {
  game: GameUpdate;
  /** The card catalog. */
  cards: Card[];
  /** True while a pick is on its way to the server. */
  disabled: boolean;
  /** The cards toggled so far, and where the choice stands with them; null while there is none to make. */
  selection: Selection;
  choice: ChoiceState | null;
  /** The cards the bot would choose, if its advice is shown. */
  advised: string[];
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

/** Over the board in the setup and each Research phase: the cards a Player chooses from, large enough to read and all in
 * view. At setup the Corporations, Prelude Cards and Project Cards dealt show in a row each, so that combinations can be
 * tried. Clicking a card toggles it, and Done is in the status bar. In the Draft, the cards kept and passed on so far
 * show above. The cards a card such as Business Contacts lets its Player look at show the same way as the Draft's. It
 * can be hidden to look at the board. */
export function BuyingPanel({ game, cards, disabled, selection, choice, advised }: Props) {
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
  const atSetup = view.phase === "setup" && board.buying !== null;
  const panel = board.keeping
    ? keepingPanel(game, shown, catalog)
    : board.drafting
      ? draftPanel(game, shown)
      : atSetup
        ? setupPanel(game, shown, catalog, selection, choice)
        : board.buying
          ? buyingPanel(game, shown, choice)
          : playingPreludeCards(game, shown)
            ? preludePlayingPanel(game, shown)
            : null;
  if (panel === null) return null;
  const kept = board.keeping?.kept ?? board.drafting?.kept;
  const waitingFor = view.current_player !== null && view.current_player !== shown ? view.current_player : null;
  const passedThisGeneration = (board.passed_in_draft ?? []).filter((pass) => pass.generation === view.generation);
  const named = (ids: string[]) => ids.map((id) => catalog.get(id)!);
  const choosing = decision?.player === shown;
  const counts = panel.rows.map((row) => row.cards.length);
  const rows = panel.rows.map((row, index) => (
    <PanelCards
      key={row.title ?? ""}
      title={row.title}
      counts={counts}
      row={index}
      cards={named(row.cards)}
      marked={row.marked ?? []}
      markedAs={row.markedAs ?? "Bought"}
      notes={row.notes ?? new Map()}
      verb={row.verb}
      selection={choosing ? selection : null}
      advised={choosing ? advised : []}
      disabled={disabled}
    />
  ));

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
        <div className="buying-panel-rows">
          {rows}
        </div>
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
  rows: Row[];
}

/** One row of cards shown large, to choose from. */
interface Row {
  title?: string;
  /** The cards' ids. */
  cards: string[];
  /** What choosing one does, for its button: "Buy". */
  verb: string;
  /** The cards chosen already, and what their mark says: "Bought", unless given. */
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
    rows: [{ cards: picking_from, verb: "Keep" }],
  };
}

/** At setup: the Corporations, Prelude Cards and Project Cards dealt to `player`, all at once. */
function setupPanel(
  game: GameUpdate,
  player: number,
  catalog: Map<string, Card>,
  selection: Selection,
  choice: ChoiceState | null,
): Panel {
  const board = game.view.players[player];
  const { choosing_corporation: corporations, prelude_cards: preludeCards, buying } = board;
  const rows: Row[] = [];
  if (corporations && corporations.dealt.length > 0) {
    rows.push({
      title: "Corporation · choose 1",
      cards: corporations.dealt,
      verb: "Choose",
      marked: corporations.picked === null ? [] : [corporations.picked],
      markedAs: "Chosen",
    });
  }
  if (preludeCards && preludeCards.dealt.length > 0) {
    rows.push({
      title: `Prelude Cards · keep ${PRELUDE_CARDS_KEPT}`,
      cards: preludeCards.dealt,
      verb: "Keep",
      marked: preludeCards.kept,
      markedAs: "Kept",
    });
  }
  rows.push({
    title: `Project Cards · buy any for ${CARD_PRICE} MegaCredits each`,
    cards: buying!.dealt,
    verb: "Buy",
    marked: buying!.bought,
  });
  const corporation = corporations?.dealt.find((card) => selection.chosen.includes(card)) ?? corporations?.picked;
  return {
    label: "Cards to choose at setup",
    heading: `Setup: ${whose(game, player)} cards`,
    summary: setupSummary(choice, corporation ? catalog.get(corporation) : undefined),
    waitingFor: "choose and buy",
    rows,
  };
}

/** "Teractor: 60 MegaCredits − 12 for 4 cards = 48 left", as far as it is chosen. */
function setupSummary(choice: ChoiceState | null, corporation: Card | undefined): string {
  if (!choice) return "Hidden until every Player is done";
  const bought = choice.spent / CARD_PRICE;
  const cards = `${bought} ${bought === 1 ? "card" : "cards"}`;
  if (choice.budget === null || choice.budget === undefined) return `${cards}, ${choice.spent} MegaCredits`;
  const start = corporation ? `${corporation.name}: ${startingMegaCredits(corporation)}` : `${choice.budget}`;
  return `${start} MegaCredits − ${choice.spent} for ${cards} = ${choice.budget - choice.spent} left`;
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
        : "Play the last one",
    waitingFor: "play Prelude Cards",
    rows: [
      {
        cards: kept,
        verb: "Play",
        notes: new Map(
          unplayable.map((option) => [option.details.card as string, "Can't be played: discard for 15 MegaCredits"]),
        ),
      },
    ],
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
      rows: [{ cards: looking_at, verb: "Buy" }],
    };
  }
  return {
    label: "Cards to keep",
    heading: `${name}: ${whose(game, player)} top ${looked} cards from the deck`,
    summary: `Keep ${keep} more and discard the rest · ${kept.length} kept`,
    waitingFor: "keep cards",
    rows: [{ cards: looking_at, verb: "Keep" }],
  };
}

/** In a Research phase: the cards dealt to `player` (or kept in the Draft) to buy from. */
function buyingPanel(game: GameUpdate, player: number, choice: ChoiceState | null): Panel {
  const { dealt, bought, megacredits } = game.view.players[player].buying!;
  const toggled = choice ? choice.spent / CARD_PRICE : 0;
  const count = bought.length + toggled;
  return {
    label: "Cards to buy",
    heading: `Research phase: ${whose(game, player)} ${dealt.length} cards`,
    summary: `${count} to buy, ${count * CARD_PRICE} of ${megacredits} MegaCredits · ${CARD_PRICE} each`,
    waitingFor: "buy",
    rows: [{ cards: dealt, verb: "Buy", marked: bought }],
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
  title?: string;
  /** How many cards each row has, and which of the rows this is. */
  counts: number[];
  row: number;
  cards: Card[];
  /** The ids of the cards chosen already, bought or kept, and the ribbon on them. */
  marked: string[];
  markedAs: string;
  /** A ribbon on some of the cards, by id. */
  notes: Map<string, string>;
  /** What choosing a card does: "Buy" or "Keep". */
  verb: string;
  /** The cards toggled, while the Player shown decides. */
  selection: Selection | null;
  /** The cards the bot would choose. */
  advised: string[];
  disabled: boolean;
}

/** The cards to choose from: clicking one toggles it. */
function PanelCards({
  title,
  counts,
  row,
  cards,
  marked,
  markedAs,
  notes,
  verb,
  selection,
  advised,
  disabled,
}: PanelCardsProps) {
  const cardsRef = useRef<HTMLDivElement>(null);
  // A single row takes as many lines as let its cards be largest; of several, each has one line.
  const single = counts.length === 1;
  const fitted = useFitZoom(cardsRef, cards.length, GAP);
  const inRow = useRowZoom(cardsRef, counts, row, SETUP_GAP);
  const style = { zoom: single ? fitted : inRow };
  return (
    <div className="buying-panel-row">
      {title && <h3>{title}</h3>}
      <div ref={cardsRef} className="buying-panel-cards" style={{ gap: single ? GAP : SETUP_GAP }}>
        {cards.map((card) => {
          const isMarked = marked.includes(card.id);
          const isChosen = selection?.chosen.includes(card.id) ?? false;
          const note = notImplementedNote(card);
          const ribbon = notes.get(card.id);
          const face = (
            <>
              <PrintedCard card={card} />
              {isMarked && <span className="card-ribbon bought">{markedAs}</span>}
              {isChosen && <span className="card-ribbon chosen">✓</span>}
              {advised.includes(card.id) && <span className="card-ribbon advised">Bot's pick</span>}
              {note && <span className="card-ribbon not-implemented">Not implemented</span>}
              {ribbon && <span className="card-ribbon not-implemented">{ribbon}</span>}
            </>
          );
          if (selection?.offers(card.id)) {
            return (
              <button
                key={card.id}
                className={`buy-card buyable ${isChosen ? "chosen" : ""}`}
                style={style}
                disabled={disabled}
                title={ribbon ?? note}
                aria-label={`${verb} ${card.name}${ribbon ? `: ${ribbon}` : ""}`}
                aria-pressed={isChosen}
                onClick={() => selection.toggle(card.id)}
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
    </div>
  );
}
