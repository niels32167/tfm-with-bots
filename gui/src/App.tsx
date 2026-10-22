import { useState } from "react";

import { FinalScores } from "./components/FinalScores";
import { GameLog } from "./components/GameLog";
import { PlayerBoards } from "./components/PlayerBoards";
import { StatusBar } from "./components/StatusBar";
import { TemperatureTrack } from "./components/TemperatureTrack";
import type { Controller } from "./types";
import { useGameServer } from "./useGameServer";

// Until the setup screen exists, a new Game is you against one Random Bot.
const HUMAN_AGAINST_RANDOM_BOT: Controller[] = ["human", "random_bot"];

export function App() {
  const { connected, game, log, error, pickedSequence, newGame, pick } = useGameServer();
  const [showScores, setShowScores] = useState(true);

  const startNewGame = () => {
    setShowScores(true);
    newGame(HUMAN_AGAINST_RANDOM_BOT);
  };

  if (!connected) {
    return (
      <main className="splash">
        <h1>Terraforming Mars</h1>
        <p>Connecting to the local server…</p>
        <p className="hint">
          Start it with <code>uv run python -m server</code> in the project folder.
        </p>
      </main>
    );
  }

  if (!game) {
    return (
      <main className="splash">
        <h1>Terraforming Mars</h1>
        <p>Play an Asteroid-only Game against a Random Bot.</p>
        <button className="option big" onClick={startNewGame}>
          New Game
        </button>
      </main>
    );
  }

  const scores = game.view.scores;
  return (
    <div className="game">
      <header className="top-bar">
        <h1>Terraforming Mars</h1>
        <span className="generation">Generation {game.view.generation}</span>
        {scores && !showScores && (
          <button className="link-button" onClick={() => setShowScores(true)}>
            Show final scores
          </button>
        )}
        <button
          className="link-button"
          onClick={() => {
            if (scores || window.confirm("Abandon this Game and start a new one?")) startNewGame();
          }}
        >
          New Game
        </button>
      </header>
      <StatusBar game={game} error={error} pickedSequence={pickedSequence} onPick={pick} />
      <div className="table">
        <main className="board-area">
          <TemperatureTrack temperature={game.view.temperature} />
          <div className="mars" aria-hidden="true" />
        </main>
        <aside className="side-panel">
          <PlayerBoards game={game} />
          <GameLog log={log} />
        </aside>
      </div>
      {scores && showScores && (
        <FinalScores
          game={game}
          scores={scores}
          onClose={() => setShowScores(false)}
          onNewGame={startNewGame}
        />
      )}
    </div>
  );
}
