import { PLAYER_COLOURS, playerTitle } from "../players";
import type { Score } from "../types";
import type { GameState } from "../useGameServer";

interface Props {
  game: GameState;
  scores: Score[];
  onNewGame: () => void;
}

/** The final score screen. For now a score is just Terraform Rating. */
export function FinalScores({ game, scores, onNewGame }: Props) {
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
                  {playerTitle(game, score.player) === "You" && " (you)"}
                </td>
                <td>{score.terraform_rating}</td>
                <td className="total">{score.total}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <button className="option" onClick={onNewGame}>
          New Game
        </button>
      </div>
    </div>
  );
}
