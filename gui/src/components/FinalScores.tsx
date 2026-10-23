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

// The breakdown of a score, in the order it is counted; these columns add up to the total.
const BREAKDOWN: { key: keyof Score; heading: string }[] = [
  { key: "terraform_rating", heading: "Terraform Rating" },
  { key: "milestones", heading: "Milestones" },
  { key: "awards", heading: "Awards" },
  { key: "greeneries", heading: "Greeneries" },
  { key: "cities", heading: "Cities" },
  { key: "cards", heading: "Cards" },
];

/** The final score screen: each Player's breakdown, total and rank, best first. */
export function FinalScores({ game, scores, onClose, onUndo, onNewGame }: Props) {
  const ranked = [...scores].sort((a, b) => a.rank - b.rank || a.player - b.player);
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
              {BREAKDOWN.map(({ key, heading }) => (
                <th key={key} className="number">
                  {heading}
                </th>
              ))}
              <th className="number">Total</th>
              <th className="number" title="Breaks a tie on Victory Points">
                MegaCredits
              </th>
            </tr>
          </thead>
          <tbody>
            {ranked.map((score) => (
              <tr key={score.player} className={score.rank === 1 ? "winner" : undefined}>
                <td>{score.rank}</td>
                <td>
                  <span className="player-dot" style={{ background: PLAYER_COLOURS[score.player] }} />{" "}
                  {game.view.players[score.player].name}
                  {isYou(game, score.player) && " (you)"}
                </td>
                {BREAKDOWN.map(({ key }) => (
                  <td key={key} className="number">
                    {score[key]}
                  </td>
                ))}
                <td className="number total">{score.total}</td>
                <td className="number tiebreak">{score.megacredits}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="final-scores-hint">
          On equal totals, the Player with more MegaCredits ranks higher. The game log lists each Award's places.
        </p>
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
