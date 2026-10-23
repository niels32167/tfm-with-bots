import { useState } from "react";

import { CardGallery } from "./cards/CardGallery";
import { PlayerCards } from "./cards/PlayerCards";
import { DEFAULT_BOT_DELAY } from "./components/BotSpeedSelect";
import { FinalScores } from "./components/FinalScores";
import { GameLog } from "./components/GameLog";
import { MarsBoard } from "./components/MarsBoard";
import { MilestonesAwards } from "./components/MilestonesAwards";
import { NewGameSetup } from "./components/NewGameSetup";
import { OceanTrack } from "./components/OceanTrack";
import { PlayerBoards } from "./components/PlayerBoards";
import { StatusBar } from "./components/StatusBar";
import { TemperatureTrack } from "./components/TemperatureTrack";
import { TopBar } from "./components/TopBar";
import type { Controller, NewGameSettings } from "./types";
import { useGameServer } from "./useGameServer";

// The setup screen's first suggestion: you against one Random Bot.
const HUMAN_AGAINST_RANDOM_BOT: Controller[] = ["human", "random_bot"];

export function App() {
  const server = useGameServer();
  const { connected, game, log, error, pickedSequence } = server;
  const [settingUp, setSettingUp] = useState(false);
  const [showScores, setShowScores] = useState(true);
  const [showCards, setShowCards] = useState(false);

  // An error shown so far belongs to the Game screen, not to the setup.
  const openSetup = () => {
    server.clearError();
    setSettingUp(true);
  };
  // Starting or loading a Game leaves the setup screen and shows the next final scores.
  const startNewGame = (settings: NewGameSettings) => {
    setSettingUp(false);
    setShowScores(true);
    server.newGame(settings);
  };
  const loadReplay = (file: File, botDelay: number) => {
    setSettingUp(false);
    setShowScores(true);
    void server.loadReplay(file, botDelay);
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

  const cardGallery = showCards && <CardGallery cards={server.cards} onClose={() => setShowCards(false)} />;

  if (!game || settingUp) {
    return (
      <>
        <NewGameSetup
          initialControllers={game?.controllers ?? HUMAN_AGAINST_RANDOM_BOT}
          initialBotDelay={game?.bot_delay ?? DEFAULT_BOT_DELAY}
          error={error}
          onStart={startNewGame}
          onLoad={loadReplay}
          onShowCards={() => setShowCards(true)}
          onCancel={game ? () => setSettingUp(false) : undefined}
        />
        {cardGallery}
      </>
    );
  }

  const scores = game.view.scores;
  // True while a pick is on its way to the server.
  const picking = pickedSequence === game.decision?.sequence;
  return (
    <div className="game">
      <TopBar
        game={game}
        onShowScores={scores && !showScores ? () => setShowScores(true) : undefined}
        onShowCards={() => setShowCards(true)}
        onNewGame={openSetup}
        onUndo={server.undo}
        onSaveReplay={server.saveReplay}
        onLoadReplay={(file) => loadReplay(file, game.bot_delay)}
        onBotDelay={server.setBotDelay}
      />
      <StatusBar
        game={game}
        cards={server.cards}
        error={error}
        disabled={picking}
        onPick={server.pick}
      />
      <div className="table">
        <main className="board-area">
          <div className="mars-and-tracks">
            <TemperatureTrack temperature={game.view.temperature} />
            <div className="mars-column">
              <MarsBoard
                board={game.view.board}
                oxygen={game.view.oxygen}
                playerNames={game.view.players.map((board) => board.name)}
                decision={game.decision}
                disabled={picking}
                onPick={server.pick}
              />
            </div>
            <OceanTrack oceans={game.view.oceans} />
          </div>
          <MilestonesAwards game={game} disabled={picking} onPick={server.pick} />
        </main>
        <aside className="side-panel">
          <PlayerBoards game={game} />
          <GameLog log={log} />
        </aside>
        <PlayerCards game={game} cards={server.cards} disabled={picking} onPick={server.pick} />
      </div>
      {scores && showScores && (
        <FinalScores
          game={game}
          scores={scores}
          onClose={() => setShowScores(false)}
          onUndo={game.can_undo ? server.undo : undefined}
          onNewGame={openSetup}
        />
      )}
      {cardGallery}
    </div>
  );
}
