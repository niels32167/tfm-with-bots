import { CARD_PRICE, playersAreBuying } from "../cards/BuyingPanel";
import { TILE_NAMES } from "../format";
import { playerTitle } from "../players";
import type { Card, TileType } from "../types";
import type { GameUpdate } from "../useGameServer";
import { cardBeingPaidFor, PaymentPicker } from "./PaymentPicker";

interface Props {
  game: GameUpdate;
  /** The card catalog. */
  cards: Card[];
  error: string | null;
  /** True while a pick is on its way to the server. */
  disabled: boolean;
  onPick: (sequence: number, index: number) => void;
}

// Options picked where they are drawn rather than as buttons here: Milestones and Awards in
// their bar, cards to play or sell in the hand, and cards to keep or buy in the buying panel.
const PICKED_IN_THE_BAR = new Set(["claim_milestone", "fund_award"]);
const PICKED_IN_THE_HAND = new Set(["play_card", "sell_card"]);
const PICKED_IN_THE_PANEL = new Set(["draft_card", "buy_card", "keep_card"]);

// How the status text names the Areas a Tile goes on when they are not the usual ones, by the
// Area Options' "on".
const OTHER_AREAS: Record<string, string> = {
  ocean_areas: " on an Area reserved for Oceans",
  land: " on an Area reserved for nothing",
  next_to_two_cities: " next to at least 2 Cities",
};

/** The current Decision, with its Options as buttons, like Board Game Arena's title bar. A
 * payment Decision gets the payment picker instead. */
export function StatusBar({ game, cards, error, disabled, onPick }: Props) {
  const { decision } = game;
  const options = decision?.options ?? [];
  const pickedElsewhere = (type: string) =>
    PICKED_IN_THE_BAR.has(type) || PICKED_IN_THE_HAND.has(type) || PICKED_IN_THE_PANEL.has(type);
  const buttons = options.filter((option) => !pickedElsewhere(option.details.type));
  // Where else an Action can be picked; buying and selling say so in the status text.
  const inTheBar = options.some((option) => PICKED_IN_THE_BAR.has(option.details.type));
  const inTheHand = options.some((option) => option.details.type === "play_card");
  return (
    <div className="status-bar" role="status">
      <span className="status-text">{statusText(game, cards)}</span>
      {decision?.kind === "payment" && (
        <PaymentPicker
          key={decision.sequence}
          decision={decision}
          disabled={disabled}
          onPay={(index) => onPick(decision.sequence, index)}
        />
      )}
      {decision && decision.kind !== "area" && decision.kind !== "payment" && (
        <span className="status-options">
          {buttons.map((option) => (
            <button
              key={option.index}
              className={`option option-${option.details.type}`}
              disabled={disabled}
              onClick={() => onPick(decision.sequence, option.index)}
            >
              {option.label}
            </button>
          ))}
          {(inTheHand || inTheBar) && <span className="status-hint">{elsewhereHint(inTheHand, inTheBar)}</span>}
        </span>
      )}
      {error && <span className="status-error">{error}</span>}
    </div>
  );
}

/** Where else Options are picked: "or click a highlighted card in the hand, Milestone or Award". */
function elsewhereHint(inTheHand: boolean, inTheBar: boolean): string {
  if (inTheHand && inTheBar) return "or click a highlighted card in the hand, Milestone or Award";
  return inTheHand ? "or click a highlighted card in the hand" : "or click a highlighted Milestone or Award";
}

function statusText(game: GameUpdate, cards: Card[]): string {
  const { view, decision } = game;
  if (view.phase === "over" || view.current_player === null) return "The Game is over.";
  const who = playerTitle(game, view.current_player);
  const paidFor = cards.find((card) => card.id === cardBeingPaidFor(decision));
  if (paidFor) return `${who} must choose how to pay for ${paidFor.name} (${paidFor.cost} MegaCredits):`;
  if (decision?.kind === "area") {
    const tile = decision.options[0]?.details.tile as TileType;
    const where = OTHER_AREAS[decision.options[0]?.details.on as string] ?? "";
    return `${who} must choose where to place the ${TILE_NAMES[tile]}${where}: click a highlighted Area on Mars.`;
  }
  if (decision?.kind === "production") {
    const details = decision.options[0]?.details;
    if (details?.type === "copy_production_box") {
      return `${who} must choose which of their building cards' production box Robotic Workforce copies:`;
    }
    const card = cards.find((each) => each.id === details?.card);
    return `${who} must choose how ${card?.name} changes their Production:`;
  }
  if (decision?.kind === "final_greenery") {
    return `${who} may convert plants into a Greenery before final scoring, or be done:`;
  }
  if (decision?.kind === "draft") {
    const passingTo = view.players[decision.player].drafting?.passing_to;
    const to = passingTo === undefined ? "on" : `to ${playerTitle(game, passingTo)}`;
    return `${who} must keep one of the cards above and pass the rest ${to}: click the card to keep.`;
  }
  const keeping = decision?.kind === "keep_cards" ? view.players[decision.player].keeping : null;
  if (keeping) {
    const card = cards.find((each) => each.id === keeping.card)?.name ?? "the card played";
    const count = keeping.kept.length > 0 ? `${keeping.keep} more` : `${keeping.keep}`;
    return `${who} must keep ${count} of the cards above for ${card} and discard the rest: click a card to keep.`;
  }
  if (decision?.kind === "buy_cards") {
    const bought = view.players[decision.player].buying?.bought.length ?? 0;
    return (
      `${who} may buy any of the cards above for ${CARD_PRICE} MegaCredits each: click them, then Done. ` +
      `Bought: ${bought} (${bought * CARD_PRICE} MegaCredits).`
    );
  }
  if (decision?.kind === "sell_patents") {
    const sale = decision.options.find((option) => option.details.type === "sell_card");
    const then = decision.options.some((option) => option.details.type === "done") ? ", then Done:" : ".";
    return `${who} may sell cards from the hand for ${sale?.details.megacredits} MegaCredit each: click them${then}`;
  }
  if (view.phase === "draft") return `${who} (Random Bot) is drafting cards…`;
  if (playersAreBuying(view)) return `${who} (Random Bot) is buying cards…`;
  if (view.phase === "final_greenery") return `${who} (Random Bot) is converting plants into Greeneries…`;
  if (decision) {
    if (view.actions_this_turn === 0) return `${who} must take an Action or Pass:`;
    const canEndTurn = decision.options.some((option) => option.details.type === "end_turn");
    return canEndTurn
      ? `${who} may take a second Action, end the Turn, or Pass:`
      : `${who} may take a second Action or Pass:`;
  }
  return `${who} (Random Bot) is taking their Turn…`;
}
