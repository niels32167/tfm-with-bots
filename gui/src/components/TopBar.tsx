import { useRef, useState } from "react";

import type { GameUpdate } from "../useGameServer";
import { BotSpeedSelect } from "./BotSpeedSelect";
import { LoadReplayButton } from "./LoadReplayButton";

interface Props {
  game: GameUpdate;
  onShowScores?: () => void;
  onNewGame: () => void;
  onUndo: () => void;
  onSaveReplay: () => void;
  onLoadReplay: (file: File) => void;
  onBotDelay: (delay: number) => void;
}

/** The bar above the status bar: the Generation, the seed, and the tools for undo and Replays. */
export function TopBar({ game, onShowScores, onNewGame, onUndo, onSaveReplay, onLoadReplay, onBotDelay }: Props) {
  const hasRandomBots = game.controllers.includes("random_bot");
  return (
    <header className="top-bar">
      <h1>Terraforming Mars</h1>
      <span className="generation">Generation {game.view.generation}</span>
      <SeedButton seed={game.seed} />
      {game.viewer === null && (
        <span className="badge full-view" title="Everything is shown, including what Players hide from each other.">
          Full view
        </span>
      )}
      <div className="top-bar-tools">
        {hasRandomBots && <BotSpeedSelect delay={game.bot_delay} onChange={onBotDelay} />}
        <button
          className="link-button"
          disabled={!game.can_undo}
          title="Go back to the last Decision a human answered"
          onClick={onUndo}
        >
          Undo
        </button>
        <button className="link-button" onClick={onSaveReplay}>
          Save Replay
        </button>
        <LoadReplayButton className="link-button" onLoad={onLoadReplay} />
        {onShowScores && (
          <button className="link-button" onClick={onShowScores}>
            Show final scores
          </button>
        )}
        <button className="link-button" onClick={onNewGame}>
          New Game
        </button>
      </div>
    </header>
  );
}

/** The seed, which copies itself when clicked. */
function SeedButton({ seed }: { seed: number }) {
  const [note, setNote] = useState<string | null>(null);
  const value = useRef<HTMLSpanElement>(null);
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(String(seed));
      setNote("copied");
    } catch {
      // The browser may refuse; then the seed is selected for copying by hand.
      if (value.current) window.getSelection()?.selectAllChildren(value.current);
      setNote("press Ctrl+C to copy");
    }
    window.setTimeout(() => setNote(null), 2500);
  };
  return (
    <button className="seed" title="Copy the seed" onClick={copy}>
      Seed{" "}
      <span ref={value} className="seed-value">
        {seed}
      </span>
      {note && <span className="seed-copied"> {note}</span>}
    </button>
  );
}
