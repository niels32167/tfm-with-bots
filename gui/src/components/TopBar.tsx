import { useRef, useState } from "react";

import { CardsButton } from "../cards/CardsButton";
import type { GameUpdate } from "../useGameServer";
import { BotSpeedSelect } from "./BotSpeedSelect";
import { LoadReplayButton } from "./LoadReplayButton";

interface Props {
  game: GameUpdate;
  onShowScores?: () => void;
  onShowCards: () => void;
  onNewGame: () => void;
  onUndo: () => void;
  onSaveReplay: () => void;
  onLoadReplay: (file: File) => void;
  onBotDelay: (delay: number) => void;
  devPanelOpen: boolean;
  onToggleDevPanel: () => void;
}

/** The bar above the status bar: the Generation, the seed, the card gallery, the tools for undo and
 * Replays, and the dev panel's switch. */
export function TopBar({
  game,
  onShowScores,
  onShowCards,
  onNewGame,
  onUndo,
  onSaveReplay,
  onLoadReplay,
  onBotDelay,
  devPanelOpen,
  onToggleDevPanel,
}: Props) {
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
        <CardsButton onClick={onShowCards} />
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
        <button className="link-button" aria-pressed={devPanelOpen} onClick={onToggleDevPanel}>
          Dev panel
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
