import { CARD_PRICE, playersAreBuying } from "../cards/BuyingPanel";
import { HAND_OPTIONS } from "../cards/HandDock";
import { TILE_NAMES } from "../format";
import { controllerLabel, PLAYER_COLOURS, playerTitle } from "../players";
import type { Card, ControllerOnOffer, NextCardEffect, TileType } from "../types";
import type { GameUpdate } from "../useGameServer";
import { LogLine } from "./GameLog";
import { cardBeingPaidFor, PaymentPicker } from "./PaymentPicker";

interface Props {
  game: GameUpdate;
  /** The card catalog. */
  cards: Card[];
  /** The Controllers the server offers, for their labels. */
  offered: ControllerOnOffer[];
  /** The latest line of the game log, shown while a registered Controller acts. */
  latest: string | undefined;
  error: string | null;
  /** True while a pick is on its way to the server. */
  disabled: boolean;
  onPick: (sequence: number, index: number) => void;
  onUndo: () => void;
}

// Options picked where they are drawn rather than as buttons here: Standard Projects in their panel,
// Milestones and Awards in their bar, cards to play, sell or discard in the hand, card actions on the
// played cards, and cards to keep or buy in the buying panel. (A card to give or take Card Resources is both a button
// here and a card outlined among the played cards, which may be out of view when one must be picked.)
const PICKED_IN_THE_PROJECTS = new Set(["standard_project"]);
const PICKED_IN_THE_BAR = new Set(["claim_milestone", "fund_award"]);
const PICKED_IN_THE_HAND = new Set(Object.keys(HAND_OPTIONS));
const PICKED_ON_PLAYED_CARDS = new Set(["use_action"]);
const PICKED_IN_THE_PANEL = new Set([
  "choose_corporation",
  "keep_prelude_card",
  "play_prelude_card",
  "draft_card",
  "buy_card",
  "keep_card",
]);

// How the status text names the Areas a Tile goes on when they are not the usual ones, by the
// Area Options' "on".
const OTHER_AREAS: Record<string, string> = {
  ocean_areas: " on an Area reserved for Oceans",
  land: " on an Area reserved for nothing",
  next_to_two_cities: " next to at least 2 Cities",
  next_to_no_other_tile: " next to no other Tile",
  next_to_a_city: " next to a City",
  next_to_a_greenery: " next to a Greenery",
  volcanoes: " on a volcano",
  steel_or_titanium_bonus: " on an Area with a steel or titanium bonus",
  steel_or_titanium_bonus_next_to_own_tile: " on an Area with a steel or titanium bonus, next to one of their Tiles",
  noctis_city: " on the Area reserved for it",
  phobos_space_haven: " on the Area reserved for it",
  ganymede_colony: " on the Area reserved for it",
};

/** The current Decision, with its Options as buttons and Undo at the end, like Board Game Arena's title
 * bar: a centred sentence naming the Player in their colour, and while a registered Controller acts, what it last
 * did underneath. A payment Decision gets the payment picker instead. */
export function StatusBar({ game, cards, offered, latest, error, disabled, onPick, onUndo }: Props) {
  const { decision, view } = game;
  const options = decision?.options ?? [];
  const pickedElsewhere = (type: string) =>
    [PICKED_IN_THE_PROJECTS, PICKED_IN_THE_BAR, PICKED_IN_THE_HAND, PICKED_ON_PLAYED_CARDS, PICKED_IN_THE_PANEL].some(
      (set) => set.has(type),
    );
  const buttons = options.filter((option) => !pickedElsewhere(option.details.type));
  // Where else an Action can be picked; buying and selling say so in the status text.
  const elsewhere = [
    options.some((option) => option.details.type === "play_card") && "card in the hand",
    options.some((option) => PICKED_ON_PLAYED_CARDS.has(option.details.type)) && "played card's action",
    options.some((option) => PICKED_IN_THE_PROJECTS.has(option.details.type)) && "Standard Project",
    options.some((option) => PICKED_IN_THE_BAR.has(option.details.type)) && "Milestone or Award",
  ].filter((place): place is string => Boolean(place));
  return (
    <div className="status-bar" role="status">
      <span className="status-text">
        <StatusSentence game={game} text={statusText(game, cards, offered)} />
      </span>
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
          {elsewhere.length > 0 && <span className="status-hint">{elsewhereHint(elsewhere)}</span>}
        </span>
      )}
      {game.can_undo && <UndoButton onUndo={onUndo} />}
      {error && <span className="status-error">{error}</span>}
      {!decision && view.phase !== "over" && latest && (
        <span className="status-latest">
          <LogLine line={latest} players={view.players.map((player) => player.name)} />
        </span>
      )}
    </div>
  );
}

/** Undo, in red, at the end of the status bar. */
export function UndoButton({ onUndo }: { onUndo: () => void }) {
  return (
    <button className="option undo" title="Go back to the last Decision a human answered" onClick={onUndo}>
      Undo
    </button>
  );
}

/** The sentence, with the Player it starts with in their colour. */
function StatusSentence({ game, text }: { game: GameUpdate; text: string }) {
  const { current_player: current } = game.view;
  const who = current === null ? null : playerTitle(game, current);
  if (current === null || who === null || !text.startsWith(who)) return <>{text}</>;
  return (
    <>
      <span style={{ color: PLAYER_COLOURS[current] }}>{who}</span>
      {text.slice(who.length)}
    </>
  );
}

/** Where else Options are picked: "or click a highlighted card in the hand, played card's action,
 * Standard Project, Milestone or Award". */
function elsewhereHint(places: string[]): string {
  return `or click a highlighted ${places.join(", ")}`;
}

function statusText(game: GameUpdate, cards: Card[], offered: ControllerOnOffer[]): string {
  const { view, decision } = game;
  if (view.phase === "over" || view.current_player === null) return "The Game is over.";
  const who = playerTitle(game, view.current_player);
  const bot = controllerLabel(offered, game.controllers[view.current_player]);
  const paidFor = cards.find((card) => card.id === cardBeingPaidFor(decision));
  if (paidFor && decision?.options[0].details.action) {
    const pay = (paidFor.effects?.action as { pay?: { megacredits: number } } | undefined)?.pay;
    return `${who} must choose how to pay for the action of ${paidFor.name} (${pay?.megacredits} MegaCredits):`;
  }
  if (paidFor) {
    const cost = (decision && view.players[decision.player].card_costs?.[paidFor.id]) ?? paidFor.cost;
    return `${who} must choose how to pay for ${paidFor.name} (${cost} MegaCredits):`;
  }
  if (decision?.kind === "payment" && decision.options[0].details.paying_for) {
    const { paying_for: payingFor, cost } = decision.options[0].details;
    return `${who} must choose how to pay for ${payingFor as string} (${cost as number} MegaCredits):`;
  }
  if (decision?.kind === "corporation") {
    return `${who} must choose one of the Corporations above: click the one to play.`;
  }
  if (decision?.kind === "prelude_cards") {
    const kept = view.players[decision.player].prelude_cards?.kept.length ?? 0;
    return `${who} must keep ${kept > 0 ? "one more" : "2"} of the Prelude Cards above: click a card to keep.`;
  }
  if (decision?.kind === "play_prelude_card" && view.phase === "action") {
    return `${who} must play one of the Prelude Cards drawn above, discarding the others: click the one to play.`;
  }
  if (decision?.kind === "play_prelude_card") {
    return `${who} must play both Prelude Cards above, one at a time: click the one to play first.`;
  }
  if (decision?.kind === "play_card") {
    const prelude = cards.find((each) => each.id === view.players[decision.player].next_card);
    const nextCard = prelude?.effects?.next_card as NextCardEffect | undefined;
    const how = nextCard?.ignores_global_requirements
      ? ", ignoring its global requirements"
      : nextCard?.discount
        ? ` for ${nextCard.discount} MegaCredits less`
        : "";
    return `${who} must play a card from the hand for ${prelude?.name}${how}: click a highlighted card.`;
  }
  if (decision?.options.some((option) => option.details.type === "first_action")) {
    return `${who} must take their Corporation's first action, or Pass:`;
  }
  if (decision?.kind === "resources") {
    const card = cards.find((each) => each.id === decision.options[0]?.details.card);
    return `${who} must choose what the action of ${card?.name} spends:`;
  }
  if (decision?.kind === "target") {
    const first = decision.options[0]?.details;
    const card = cards.find((each) => each.id === first?.card)?.name;
    if (first?.type === "lower_production") return `${who} must choose whose Production ${card} lowers:`;
    if (first?.type === "move_card_resource") {
      return `${who} must choose the card ${card} removes 1 ${first.kind} from: click a button or a highlighted played card.`;
    }
    if (decision.options.some((option) => option.details.type === "remove_card_resources")) {
      return `${who} may choose what ${card} removes: click a button or a highlighted played card.`;
    }
    const steals = decision.options.some((option) => option.details.stolen);
    return `${who} may choose whom ${card} ${steals ? "steals" : "removes"} Resources from:`;
  }
  if (decision?.kind === "effects") {
    const card = cards.find((each) => each.id === decision.options[0]?.details.card);
    return `${who} must choose what ${card?.effects?.action ? "the action of " : ""}${card?.name} does:`;
  }
  if (decision?.kind === "viral_enhancers") {
    const card = cards.find((each) => each.id === decision.options[0]?.details.card);
    return `${who} must choose what Viral Enhancers does for a Tag of ${card?.name}:`;
  }
  if (decision?.kind === "add_to_card") {
    const card = cards.find((each) => each.id === decision.options[0]?.details.card);
    return `${who} must choose the card ${card?.name} adds to: click a button or a highlighted played card.`;
  }
  if (decision?.kind === "olympus_conference") {
    const discard = decision.options.some((option) => option.details.type === "discard_card");
    const first = discard ? ", or may first discard a card from the hand to draw one (Mars University)" : "";
    return `${who} must choose what Olympus Conference does for the science Tag played${first}:`;
  }
  if (decision?.kind === "area") {
    const details = decision.options[0]?.details;
    if (details?.type === "claim_area") {
      return `${who} must choose the Area to claim with Land Claim: click a highlighted Area on Mars.`;
    }
    const special = cards.find((each) => each.id === details?.card)?.name;
    const tile = special ? `${special} Tile` : TILE_NAMES[details?.tile as TileType];
    const where = OTHER_AREAS[details?.on as string] ?? "";
    return `${who} must choose where to place the ${tile}${where}: click a highlighted Area.`;
  }
  if (decision?.kind === "production") {
    const details = decision.options[0]?.details;
    if (details?.type === "copy_production_box") {
      return `${who} must choose which of their building cards' production box Robotic Workforce copies:`;
    }
    const card = cards.find((each) => each.id === details?.card);
    return `${who} must choose how ${card?.name} changes their Production:`;
  }
  if (decision?.kind === "free_award") {
    return `${who} must fund an Award for free, as their Corporation's first action: click a highlighted Award.`;
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
  if (keeping && keeping.price > 0) {
    const card = cards.find((each) => each.id === keeping.card)?.name ?? "the card";
    return (
      `${who} may buy the card above for ${keeping.price} MegaCredits with the action of ${card}: ` +
      "click it, or Done to discard it."
    );
  }
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
  if (decision?.kind === "discard_to_draw") {
    return `${who} may discard a card from the hand to draw one (Mars University): click it, or Done to keep the hand.`;
  }
  if (view.phase === "draft") return `${who} (${bot}) is drafting cards…`;
  if (view.phase === "prelude_cards") return `${who} (${bot}) is playing their Prelude Cards…`;
  if (playersAreBuying(view)) return `${who} (${bot}) is choosing and buying cards…`;
  if (view.phase === "final_greenery") return `${who} (${bot}) is converting plants into Greeneries…`;
  if (decision) {
    if (view.actions_this_turn === 0) return `${who} must take an Action or Pass:`;
    const canEndTurn = decision.options.some((option) => option.details.type === "end_turn");
    return canEndTurn
      ? `${who} may take a second Action, end the Turn, or Pass:`
      : `${who} may take a second Action or Pass:`;
  }
  return `${who} (${bot}) is taking their Turn…`;
}
