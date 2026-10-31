import { playersAreBuying } from "../cards/BuyingPanel";
import { useCardsById } from "../cards/catalog";
import { signed } from "../format";
import { controllerLabel, isYou, PLAYER_COLOURS, playerTitle } from "../players";
import { type Card, type DraftPass, RESOURCES, TAGS, type CountedTag, type Resource } from "../types";
import type { GameUpdate } from "../useGameServer";

const RESOURCE_NAMES: Record<Resource, string> = {
  megacredits: "MegaCredits",
  steel: "Steel",
  titanium: "Titanium",
  plants: "Plants",
  energy: "Energy",
  heat: "Heat",
};

// As the game log names each Production: "MegaCredit Production", "plant Production".
const PRODUCTION_NAMES: Record<Resource, string> = {
  megacredits: "MegaCredit Production",
  steel: "steel Production",
  titanium: "titanium Production",
  plants: "plant Production",
  energy: "energy Production",
  heat: "heat Production",
};

// The Tags a player board counts: every Tag but the Event Tag, which never counts once played.
const COUNTED_TAGS = TAGS.filter((tag): tag is CountedTag => tag !== "event");

interface Props {
  game: GameUpdate;
  /** The card catalog. */
  cards: Card[];
}

/** One board per Player: Terraform Rating, the six Resources with their Production, Turn
 * state, the first-player marker, cards in hand, the Tags in play, and the cards they passed in
 * the Draft where the view shows them. */
export function PlayerBoards({ game, cards }: Props) {
  const { view } = game;
  const catalog = useCardsById(cards);
  return (
    <section className="player-boards" aria-label="Player boards">
      {view.players.map((board, index) => {
        const isCurrent = view.current_player === index;
        return (
          <article
            key={index}
            className={`player-board ${isCurrent ? "current" : ""}`}
            style={{ borderLeftColor: PLAYER_COLOURS[index] }}
          >
            <header className="player-board-header">
              <span className="player-dot" style={{ background: PLAYER_COLOURS[index] }} />
              <span className="player-name">{board.name}</span>
              <span className="player-controller">
                {isYou(game, index) ? "You" : controllerLabel(game, index)}
              </span>
              {view.first_player === index && (
                <span className="badge first-player" title="First player: takes the first Turn of this Generation">
                  First player
                </span>
              )}
              {board.passed && view.phase === "action" && <span className="badge passed">Passed</span>}
              {isCurrent && <span className="badge turn">{turnBadge(game)}</span>}
              <span className="terraform-rating" title="Terraform Rating">
                <span className="terraform-rating-label">TR</span> {board.terraform_rating}
              </span>
            </header>
            <dl className="player-stats">
              {RESOURCES.map((resource) => (
                <div
                  key={resource}
                  className={`stat ${resource}`}
                  title={`${RESOURCE_NAMES[resource]} (${PRODUCTION_NAMES[resource]})`}
                >
                  <dt>{RESOURCE_NAMES[resource]}</dt>
                  <dd>
                    <span className="stat-value">{board.resources[resource]}</span>
                    <span className="stat-production">{signed(board.production[resource])}</span>
                  </dd>
                </div>
              ))}
            </dl>
            <div className="player-cards-summary">
              <span className="hand-size" title="Cards in hand">
                Hand {board.hand_size}
              </span>
              {board.next_card && (
                <span className="badge next-card" title={`${catalog.get(board.next_card)?.name}: the next card they play this Generation`}>
                  Next card: {nextCardEffect(catalog.get(board.next_card))}
                </span>
              )}
              {COUNTED_TAGS.filter((tag) => board.tags[tag] > 0).map((tag) => (
                <span key={tag} className="tag-count" title={`${board.tags[tag]} ${tag} Tags in play`}>
                  <img src={`/card-list/images/tags/${tag}.png`} alt={`${tag} Tags`} />
                  {board.tags[tag]}
                </span>
              ))}
            </div>
            {board.passed_in_draft && board.passed_in_draft.length > 0 && (
              <PassedInDraft
                game={game}
                passes={board.passed_in_draft}
                name={(id) => catalog.get(id)?.name ?? id}
              />
            )}
          </article>
        );
      })}
    </section>
  );
}

/** What an Event such as Indentured Workers changes about the next card played: "−8 MegaCredits",
 * "±2 steps on global Requirements". */
function nextCardEffect(card: Card | undefined): string {
  const effect = card?.effects?.next_card as { discount?: number; requirement_steps?: number } | undefined;
  const parts = [
    effect?.discount && `−${effect.discount} MegaCredits`,
    effect?.requirement_steps && `±${effect.requirement_steps} steps on global Requirements`,
  ];
  return parts.filter(Boolean).join(", ");
}

interface PassedInDraftProps {
  game: GameUpdate;
  passes: DraftPass[];
  /** A card's name, by its id. */
  name: (id: string) => string;
}

/** The cards a Player passed on in the Draft this Game, folded away: by Generation, whom they went
 * to and each set passed, latest first. */
function PassedInDraft({ game, passes, name }: PassedInDraftProps) {
  const generations = [...new Set(passes.map((pass) => pass.generation))].reverse();
  const count = passes.reduce((total, pass) => total + pass.cards.length, 0);
  return (
    <details className="passed-in-draft">
      <summary>Passed in the Draft ({count} cards)</summary>
      {generations.map((generation) => {
        const passed = passes.filter((pass) => pass.generation === generation);
        return (
          <div key={generation} className="passed-in-draft-generation">
            <h4>
              Generation {generation}, to {playerTitle(game, passed[0].to)}
            </h4>
            <ul>
              {passed.map((pass, index) => (
                <li key={index}>{pass.cards.map(name).join(", ")}</li>
              ))}
            </ul>
          </div>
        );
      })}
    </details>
  );
}

/** What the current Player is doing: their Turn (and which Action), the Draft, buying cards, or
 * the final Greenery conversion. */
function turnBadge(game: GameUpdate): string {
  const { view } = game;
  if (view.phase === "final_greenery") return "Final Greeneries";
  if (view.phase === "draft") return "Drafting";
  if (playersAreBuying(view)) return "Buying cards";
  return `Turn${view.actions_this_turn > 0 ? ` · Action ${view.actions_this_turn + 1}` : ""}`;
}
