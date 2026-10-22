import { controllerLabel, PLAYER_COLOURS, playerTitle } from "../players";
import type { GameState } from "../useGameServer";

/** One board per Player: MegaCredits and their Production, Terraform Rating, and Turn state. */
export function PlayerBoards({ game }: { game: GameState }) {
  const { view } = game;
  return (
    <section className="player-boards" aria-label="Player boards">
      {view.players.map((board, index) => {
        const isCurrent = view.current_player === index;
        const production = board.production.megacredits;
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
                {playerTitle(game, index) === "You" ? "You" : controllerLabel(game, index)}
              </span>
              {board.passed && <span className="badge passed">Passed</span>}
              {isCurrent && (
                <span className="badge turn">
                  Turn{view.actions_this_turn > 0 ? ` · Action ${view.actions_this_turn + 1}` : ""}
                </span>
              )}
            </header>
            <dl className="player-stats">
              <div className="stat megacredits" title="MegaCredits (MegaCredit Production)">
                <dt>MegaCredits</dt>
                <dd>
                  <span className="stat-value">{board.megacredits}</span>
                  <span className="stat-production">
                    {production >= 0 ? `+${production}` : `−${-production}`}
                  </span>
                </dd>
              </div>
              <div className="stat terraform-rating" title="Terraform Rating">
                <dt>Terraform Rating</dt>
                <dd>
                  <span className="stat-value">{board.terraform_rating}</span>
                </dd>
              </div>
            </dl>
          </article>
        );
      })}
    </section>
  );
}
