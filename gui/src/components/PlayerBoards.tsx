import { signed } from "../format";
import { controllerLabel, isYou, PLAYER_COLOURS } from "../players";
import { RESOURCES, TAGS, type CountedTag, type Resource } from "../types";
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

/** One board per Player: Terraform Rating, the six Resources with their Production, Turn
 * state, the first-player marker, cards in hand and the Tags in play. */
export function PlayerBoards({ game }: { game: GameUpdate }) {
  const { view } = game;
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
              {COUNTED_TAGS.filter((tag) => board.tags[tag] > 0).map((tag) => (
                <span key={tag} className="tag-count" title={`${board.tags[tag]} ${tag} Tags in play`}>
                  <img src={`/card-list/images/tags/${tag}.png`} alt={`${tag} Tags`} />
                  {board.tags[tag]}
                </span>
              ))}
            </div>
          </article>
        );
      })}
    </section>
  );
}

/** What the current Player is doing: their Turn (and which Action), or the final Greenery conversion. */
function turnBadge(game: GameUpdate): string {
  const { view } = game;
  if (view.phase === "final_greenery") return "Final Greeneries";
  return `Turn${view.actions_this_turn > 0 ? ` · Action ${view.actions_this_turn + 1}` : ""}`;
}
