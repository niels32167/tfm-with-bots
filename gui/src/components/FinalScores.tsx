import { isYou, PLAYER_COLOURS } from "../players";
import type { Score } from "../types";
import type { GameUpdate } from "../useGameServer";

interface Props {
  game: GameUpdate;
  scores: Score[];
  onClose: () => void;
  /** Goes back to the last human Decision; absent when there is none. */
  onUndo?: () => void;
  onNewGame: () => void;
}

/** The final score screen. For now a score is just Terraform Rating. */
export function FinalScores({ game, scores, onClose, onUndo, onNewGame }: Props) {
  const ranked = [...scores].sort((a, b) => b.total - a.total);
  return (
    <div className="overlay" role="dialog" aria-labelledby="final-scores-title">
      <div className="final-scores">
        <h2 id="final-scores-title">Final scores</h2>
        <p className="final-scores-generation">The Game ended after Generation {game.view.generation}.</p>
        <table>
          <thead>
            <tr>
              <th>Rank</th>
              <th>Player</th>
              <th>Terraform Rating</th>
              <th>Total</th>
            </tr>
          </thead>
          <tbody>
            {ranked.map((score) => (
              <tr key={score.player}>
                <td>{1 + ranked.filter((other) => other.total > score.total).length}</td>
                <td>
                  <span className="player-dot" style={{ background: PLAYER_COLOURS[score.player] }} />{" "}
                  {game.view.players[score.player].name}
                  {isYou(game, score.player) && " (you)"}
                </td>
                <td>{score.terraform_rating}</td>
                <td className="total">{score.total}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="final-scores-buttons">
          <button className="link-button" onClick={onClose}>
            Back to the board
          </button>
          {onUndo && (
            <button className="link-button" onClick={onUndo}>
              Undo
            </button>
          )}
          <button className="option" onClick={onNewGame}>
            New Game
          </button>
        </div>
      </div>
    </div>
  );
}
