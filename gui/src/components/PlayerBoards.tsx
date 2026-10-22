import { signed } from "../format";
import { controllerLabel, isYou, PLAYER_COLOURS } from "../players";
import type { GameUpdate } from "../useGameServer";

/** One board per Player: Resources, MegaCredit Production, Terraform Rating, Turn state and the first-player marker. */
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
                  <span className="stat-production">{signed(board.production.megacredits)}</span>
                </dd>
              </div>
              <div className="stat steel" title="Steel">
                <dt>Steel</dt>
                <dd>
                  <span className="stat-value">{board.steel}</span>
                </dd>
              </div>
              <div className="stat titanium" title="Titanium">
                <dt>Titanium</dt>
                <dd>
                  <span className="stat-value">{board.titanium}</span>
                </dd>
              </div>
              <div className="stat plants" title="Plants">
                <dt>Plants</dt>
                <dd>
                  <span className="stat-value">{board.plants}</span>
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
