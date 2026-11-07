import { useEffect, useState } from "react";

import { BuyingPanel, cardsShownFor } from "./cards/BuyingPanel";
import { CardGallery } from "./cards/CardGallery";
import { CardZoom } from "./cards/CardZoom";
import { HandDock, handOptions } from "./cards/HandDock";
import { PlayedCards } from "./cards/PlayedCards";
import { DEFAULT_BOT_DELAY } from "./components/BotSpeedSelect";
import { DevPanel } from "./components/DevPanel";
import { FinalScores } from "./components/FinalScores";
import { GameLog } from "./components/GameLog";
import { GlobalReadings } from "./components/GlobalReadings";
import { MarsBoard } from "./components/MarsBoard";
import { NewGameSetup } from "./components/NewGameSetup";
import { PlayerBoards } from "./components/PlayerBoards";
import { StatusBar, UndoButton } from "./components/StatusBar";
import { TopBar } from "./components/TopBar";
import { type ControllerName, HUMAN, type NewGameSettings, type Scenario } from "./types";
import { type GameUpdate, useGameServer } from "./useGameServer";

// The setup screen's first suggestion: you against one Random Bot.
const HUMAN_AGAINST_RANDOM_BOT: ControllerName[] = [HUMAN, "random_bot"];

export function App() {
  const server = useGameServer();
  const { connected, game, log, devView, error, pickedSequence } = server;
  const [settingUp, setSettingUp] = useState(false);
  const [showScores, setShowScores] = useState(true);
  const [showCards, setShowCards] = useState(false);
  const [handFolded, setHandFolded] = useState(false);
  const [devPanelOpen, setDevPanelOpen] = useState(false);
  // The step the dev panel looks at, or null for the latest, and whether it shows the full view.
  const [devStep, setDevStep] = useState<number | null>(null);
  const [fullViewOn, setFullViewOn] = useState(false);
  // While the dev panel is open it follows the Game, and each look leaves the Game as it is.
  const { askForDevView } = server;
  useEffect(() => {
    if (devPanelOpen && game) askForDevView(devStep);
  }, [devPanelOpen, devStep, game, askForDevView]);
  // Once the Game has gone back behind the step looked at, or is another Game, it follows the Game
  // again, so a human's Decision is never left hidden behind a step that no longer exists.
  useEffect(() => {
    setDevStep((step) => (devView && step !== null && step >= devView.steps ? null : step));
  }, [devView]);
  // Which Game the dev panel looks at: another one starts it afresh, without an old position to edit.
  const [devPanelKey, setDevPanelKey] = useState(0);

  // The hand unfolds when a new Decision lets a card in it be played or sold; it can be folded again.
  const handHasOptions = handOptions(game?.decision ?? null).size > 0;
  useEffect(() => {
    if (handHasOptions) setHandFolded(false);
  }, [game?.decision?.sequence, handHasOptions]);

  const closeDevPanel = () => {
    setDevPanelOpen(false);
    setDevStep(null);
  };
  const startFromScenario = (scenario: Scenario) => {
    if (!game) return;
    setShowScores(true);
    server.startFromScenario(scenario, game.controllers, game.bot_delay);
  };
  // An error shown so far belongs to the Game screen, not to the setup.
  const openSetup = () => {
    server.clearError();
    setSettingUp(true);
  };
  // Starting or loading a Game leaves the setup screen and shows the next final scores.
  const startNewGame = (settings: NewGameSettings) => {
    setSettingUp(false);
    setDevStep(null);
    setDevPanelKey((key) => key + 1);
    setShowScores(true);
    server.newGame(settings);
  };
  const loadReplay = (file: File, botDelay: number) => {
    setSettingUp(false);
    setDevStep(null);
    setDevPanelKey((key) => key + 1);
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
          offered={server.controllers}
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

  // What the screen shows: the Game as this GUI's update has it, unless the dev panel looks at an
  // earlier step, where nothing can be picked, or shows the full view.
  const lookingBack = devPanelOpen && devStep !== null && devView !== null && devView.step < devView.steps;
  const showingFullView = devPanelOpen && fullViewOn && devView !== null;
  const atDevStep = lookingBack ? { view: devView.view, decision: null } : {};
  const shown: GameUpdate = {
    ...game,
    ...atDevStep,
    ...(showingFullView ? { viewer: null, view: devView.full_view } : {}),
  };
  const scores = shown.view.scores;
  // True while a pick is on its way to the server.
  const picking = pickedSequence === shown.decision?.sequence;
  return (
    <div className={`game ${handFolded ? "hand-dock-folded" : ""} ${devPanelOpen ? "dev-panel-open" : ""}`}>
      <TopBar
        game={shown}
        onShowScores={scores && !showScores ? () => setShowScores(true) : undefined}
        onShowCards={() => setShowCards(true)}
        onNewGame={openSetup}
        onSaveReplay={server.saveReplay}
        onLoadReplay={(file) => loadReplay(file, game.bot_delay)}
        onBotDelay={server.setBotDelay}
        devPanelOpen={devPanelOpen}
        onToggleDevPanel={() => (devPanelOpen ? closeDevPanel() : setDevPanelOpen(true))}
      />
      <div className="table">
        <div className="table-main">
          {lookingBack ? (
            <div className="status-bar dev-looking-back">
              Looking back at step {devView.step} of {devView.steps}: nothing can be picked here, and the Game carries on
              without it.
              {game.can_undo && <UndoButton onUndo={server.undo} />}
            </div>
          ) : (
            <StatusBar
              game={shown}
              cards={server.cards}
              offered={server.controllers}
              latest={log.at(-1)}
              error={error}
              disabled={picking}
              onPick={server.pick}
              onUndo={server.undo}
            />
          )}
          <main className="board-area">
            {cardsShownFor(shown) !== null && (
              <BuyingPanel game={shown} cards={server.cards} disabled={picking} onPick={server.pick} />
            )}
            <MarsBoard game={shown} cards={server.cards} disabled={picking} onPick={server.pick} />
          </main>
          <PlayedCards game={shown} cards={server.cards} disabled={picking} onPick={server.pick} />
        </div>
        <aside className="side-panel">
          <GlobalReadings view={shown.view} />
          <PlayerBoards game={shown} cards={server.cards} offered={server.controllers} />
          <GameLog log={lookingBack ? devView.log : log} players={shown.view.players.map((board) => board.name)} />
        </aside>
      </div>
      <HandDock
        game={shown}
        cards={server.cards}
        disabled={picking}
        onPick={server.pick}
        folded={handFolded}
        onFold={setHandFolded}
      />
      {scores && showScores && (
        <FinalScores
          game={shown}
          scores={scores}
          onClose={() => setShowScores(false)}
          onUndo={game.can_undo ? server.undo : undefined}
          onNewGame={openSetup}
        />
      )}
      {cardGallery}
      <CardZoom cards={server.cards} />
      {devPanelOpen && (
        <DevPanel
          key={devPanelKey}
          cards={server.cards}
          shown={devView}
          step={devStep}
          onStep={setDevStep}
          fullView={fullViewOn}
          onFullView={setFullViewOn}
          viewer={game.viewer}
          error={error}
          onStartFrom={startFromScenario}
          onClose={closeDevPanel}
        />
      )}
    </div>
  );
}
