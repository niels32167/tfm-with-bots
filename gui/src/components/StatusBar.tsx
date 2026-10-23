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
// their bar, and cards in the hand.
const PICKED_IN_THE_BAR = new Set(["claim_milestone", "fund_award"]);
const PICKED_IN_THE_HAND = new Set(["play_card"]);

/** The current Decision, with its Options as buttons, like Board Game Arena's title bar. A
 * payment Decision gets the payment picker instead. */
export function StatusBar({ game, cards, error, disabled, onPick }: Props) {
  const { decision } = game;
  const options = decision?.options ?? [];
  const pickedElsewhere = (type: string) => PICKED_IN_THE_BAR.has(type) || PICKED_IN_THE_HAND.has(type);
  const buttons = options.filter((option) => !pickedElsewhere(option.details.type));
  const inTheBar = options.some((option) => PICKED_IN_THE_BAR.has(option.details.type));
  const inTheHand = options.some((option) => PICKED_IN_THE_HAND.has(option.details.type));
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
    return `${who} must choose where to place the ${TILE_NAMES[tile]}: click a highlighted Area on Mars.`;
  }
  if (decision?.kind === "final_greenery") {
    return `${who} may convert plants into a Greenery before final scoring, or be done:`;
  }
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
