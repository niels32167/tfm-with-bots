import { playerTitle } from "../players";
import type { GameState } from "../useGameServer";

interface Props {
  game: GameState;
  error: string | null;
  pickedSequence: number | null;
  onPick: (sequence: number, index: number) => void;
}

/** The current Decision, with its Options as buttons, like Board Game Arena's title bar. */
export function StatusBar({ game, error, pickedSequence, onPick }: Props) {
  const { decision } = game;
  return (
    <div className="status-bar" role="status">
      <span className="status-text">{statusText(game)}</span>
      {decision && (
        <span className="status-options">
          {decision.options.map((option) => (
            <button
              key={option.index}
              className={`option option-${option.details.type}`}
              disabled={pickedSequence === decision.sequence}
              onClick={() => onPick(decision.sequence, option.index)}
            >
              {option.label}
            </button>
          ))}
        </span>
      )}
      {error && <span className="status-error">{error}</span>}
    </div>
  );
}

function statusText(game: GameState): string {
  const { view, decision } = game;
  if (view.phase === "over" || view.current_player === null) return "The Game is over.";
  const who = playerTitle(game, view.current_player);
  if (decision) {
    if (view.actions_this_turn === 0) return `${who} must take an Action or Pass:`;
    const canEndTurn = decision.options.some((option) => option.details.type === "end_turn");
    return canEndTurn
      ? `${who} may take a second Action, end the Turn, or Pass:`
      : `${who} may take a second Action or Pass:`;
  }
  return `${who} (Random Bot) is taking their Turn…`;
}
