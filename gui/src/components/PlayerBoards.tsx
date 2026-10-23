import { signed } from "../format";
import { controllerLabel, isYou, PLAYER_COLOURS } from "../players";
import { RESOURCES, type Resource } from "../types";
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

/** One board per Player: Terraform Rating, the six Resources with their Production, Turn state and the first-player marker. */
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
