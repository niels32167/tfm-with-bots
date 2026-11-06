import { useState } from "react";

import { CorporationName, ResourceCells, TagCounts, TerraformRating } from "../components/PlayerBoards";
import { isYou, PLAYER_COLOURS } from "../players";
import type { Card, Decision, DecisionOption, PlayerBoard } from "../types";
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

// A Player's area has these columns, as on Board Game Arena; the Events are folded away beside them.
const COLUMNS: { key: string; label: string; holds: (card: Card) => boolean }[] = [
  { key: "headquarters", label: "Headquarters", holds: (card) => card.type === "corporation" },
  { key: "automated", label: "Automated", holds: (card) => card.type === "automated" },
  { key: "effects", label: "Effects", holds: (card) => card.type === "active" && !card.effects?.action },
  { key: "actions", label: "Actions", holds: (card) => card.type === "active" && Boolean(card.effects?.action) },
];
const EVENTS = { key: "events", label: "Events", holds: (card: Card) => card.type === "event" };

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
  remove_card_resources: "from",
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

/** Under the board: an area for each Player, the human at the screen first, as on Board Game Arena: a
 * strip with their Resources, Production and Tags, and their cards in columns by type. In a column the
 * cards overlap so that each shows its cost, title and Tags; the Events are folded away until opened. A
 * card whose action can be used now, or that the Decision offers to give or take Card Resources, is
 * outlined and clicked to do so; one whose action is used this Generation is dimmed and marked "Used".
 * A card that holds Card Resources shows how many are on it. (The hands are in the hand dock.) */
export function PlayedCards({ game, cards, disabled, onPick }: Props) {
  const catalog = useCardsById(cards);
  const [eventsOpen, setEventsOpen] = useState<number[]>([]);
  if (catalog.size === 0) return null;
  const { view, viewer } = game;
  const players = view.players.map((_, player) => player).sort((a, b) => Number(b === viewer) - Number(a === viewer));
  const toggleEvents = (player: number) =>
    setEventsOpen((open) => (open.includes(player) ? open.filter((each) => each !== player) : [...open, player]));

  return (
    <section className="player-cards" aria-label="Played cards">
      {players.map((player) => {
        const board = view.players[player];
        const inPlay = (board.corporation ? [board.corporation, ...board.played_cards] : board.played_cards).map(
          (id) => catalog.get(id)!,
        );
        const events = inPlay.filter(EVENTS.holds);
        const open = eventsOpen.includes(player);
        const columnProps = { game, board, disabled, onPick };
        return (
          <article key={player} className="player-area" style={{ borderColor: PLAYER_COLOURS[player] }}>
            <header className="player-area-header">
              <span className="player-area-name" style={{ background: PLAYER_COLOURS[player] }}>
                {isYou(game, player) ? "You" : board.name}
              </span>
              <CorporationName id={board.corporation} catalog={catalog} />
              <TerraformRating value={board.terraform_rating} />
              <ResourceCells board={board} />
              <TagCounts board={board} />
              <button
                className="events-toggle"
                aria-expanded={open}
                title={open ? "Fold the Events away" : "Show the Events played"}
                onClick={() => toggleEvents(player)}
              >
                {events.length} Events {open ? "▴" : "▾"}
              </button>
            </header>
            <div className="played-groups">
              {COLUMNS.map(({ key, label, holds }) => (
                <PlayedColumn key={key} column={key} label={label} group={inPlay.filter(holds)} {...columnProps} />
              ))}
              {open && <PlayedColumn column={EVENTS.key} label={EVENTS.label} group={events} {...columnProps} />}
            </div>
          </article>
        );
      })}
    </section>
  );
}

interface PlayedColumnProps {
  column: string;
  label: string;
  group: Card[];
  game: GameUpdate;
  board: PlayerBoard;
  disabled: boolean;
  onPick: (sequence: number, index: number) => void;
}

function PlayedColumn({ column, label, group, game, board, disabled, onPick }: PlayedColumnProps) {
  return (
    <div className={`played-group played-group-${column}`}>
      <h4>
        <span className="played-group-count">{group.length}</span> {label}
      </h4>
      <div className="card-stack">
        {group.map((card) => (
          <PlayedCard key={card.id} card={card} game={game} board={board} disabled={disabled} onPick={onPick} />
        ))}
      </div>
    </div>
  );
}

interface PlayedCardProps {
  card: Card;
  game: GameUpdate;
  board: PlayerBoard;
  disabled: boolean;
  onPick: (sequence: number, index: number) => void;
}

function PlayedCard({ card, game, board, disabled, onPick }: PlayedCardProps) {
  const { decision } = game;
  const option = cardOptions(decision).get(card.id);
  const used = board.used_actions.includes(card.id);
  const onCard = board.card_resources[card.id];
  const onCardText = onCard === undefined ? "" : cardResourcesText(card.effects?.holds as string, onCard);
  const zoomNote = [onCard !== undefined && `${onCardText} on it`, used && "Action used this Generation"]
    .filter(Boolean)
    .join(" · ");
  const zoom = { "data-zoom-card": card.id, "data-zoom-note": zoomNote || undefined };
  const badges = (used || onCard !== undefined) && (
    <span className="card-badges">
      {onCard !== undefined && (
        <span className="card-resource-badge" title={onCardText}>
          <span className="printed-card card-resource-icon">
            <span className={`resource ${card.effects?.holds as string}`} />
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
  const named = onCard === undefined ? card.name : `${card.name}, ${onCardText} on it`;
  if (decision && option !== undefined) {
    return (
      <button
        className="small-card stacked playable"
        disabled={disabled}
        aria-label={onCard === undefined ? option.label : `${option.label}, ${onCardText} on it`}
        onClick={() => onPick(decision.sequence, option.index)}
        {...zoom}
      >
        <PrintedCard card={card} />
        {badges}
      </button>
    );
  }
  // The card whose action is under way is outlined rather than dimmed.
  const state = card.id === actionUnderWay(game) ? "action-under-way" : used ? "used-action" : "";
  return (
    <div
      className={`small-card stacked ${state}`}
      tabIndex={0}
      aria-label={used ? `${named} (action used this Generation)` : named}
      {...zoom}
    >
      <PrintedCard card={card} />
      {badges}
    </div>
  );
}
