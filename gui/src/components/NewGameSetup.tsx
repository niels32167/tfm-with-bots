import { useState } from "react";

import { CardsButton } from "../cards/CardsButton";
import { CONTROLLER_LABELS, PLAYER_COLOURS } from "../players";
import { CONTROLLERS, type Controller, type NewGameSettings } from "../types";
import { BotSpeedSelect } from "./BotSpeedSelect";
import { LoadReplayButton } from "./LoadReplayButton";

const PLAYER_COUNTS = [2, 3, 4, 5];
const MAX_PLAYERS = Math.max(...PLAYER_COUNTS);

interface Props {
  /** Controllers and Random Bot delay to start from, say those of the Game being replaced. */
  initialControllers: Controller[];
  initialBotDelay: number;
  error: string | null;
  onStart: (settings: NewGameSettings) => void;
  onLoad: (file: File, botDelay: number) => void;
  onShowCards: () => void;
  /** Leaves the setup screen without starting anything; absent when there is no Game to go back to. */
  onCancel?: () => void;
}

/** The new-Game screen: Players, their Controllers, the seed, how fast Random Bots pick, and
 * whether the implemented cards are dealt first. */
export function NewGameSetup({
  initialControllers,
  initialBotDelay,
  error,
  onStart,
  onLoad,
  onShowCards,
  onCancel,
}: Props) {
  const [playerCount, setPlayerCount] = useState(initialControllers.length);
  // Five Controllers are kept, so going down to fewer Players and back up loses no choices.
  const [allControllers, setAllControllers] = useState<Controller[]>(() =>
    Array.from({ length: MAX_PLAYERS }, (_, player) => initialControllers[player] ?? "random_bot"),
  );
  const [seedText, setSeedText] = useState("");
  const [botDelay, setBotDelay] = useState(initialBotDelay);
  const [implementedCardsFirst, setImplementedCardsFirst] = useState(true);

  const controllers = allControllers.slice(0, playerCount);
  const seed = parseSeed(seedText);

  const setController = (player: number, controller: Controller) =>
    setAllControllers((previous) => previous.map((old, index) => (index === player ? controller : old)));

  const start = () => {
    if (seed === "invalid") return;
    onStart({
      controllers,
      bot_delay: botDelay,
      implemented_cards_first: implementedCardsFirst,
      ...(seed === null ? {} : { seed }),
    });
  };

  return (
    <main className="splash">
      <div className="setup">
        <h1>New Game</h1>

        <section className="setup-section" aria-labelledby="setup-players">
          <h2 id="setup-players">Players</h2>
          <div className="segmented" role="group" aria-label="Number of Players">
            {PLAYER_COUNTS.map((count) => (
              <button
                key={count}
                className={count === playerCount ? "selected" : ""}
                aria-pressed={count === playerCount}
                onClick={() => setPlayerCount(count)}
              >
                {count}
              </button>
            ))}
          </div>
          <ol className="setup-players">
            {controllers.map((controller, player) => (
              <li key={player} className="setup-player">
                <span className="player-dot" style={{ background: PLAYER_COLOURS[player] }} />
                <span className="setup-player-name">Player {player + 1}</span>
                <div className="segmented" role="group" aria-label={`Player ${player + 1}'s Controller`}>
                  {CONTROLLERS.map((candidate) => (
                    <button
                      key={candidate}
                      className={candidate === controller ? "selected" : ""}
                      aria-pressed={candidate === controller}
                      onClick={() => setController(player, candidate)}
                    >
                      {CONTROLLER_LABELS[candidate]}
                    </button>
                  ))}
                </div>
              </li>
            ))}
          </ol>
          <p className="setup-hint">{viewHint(controllers)}</p>
        </section>

        <section className="setup-section setup-row">
          <label className="setup-seed">
            Seed{" "}
            <input
              type="text"
              inputMode="numeric"
              placeholder="random"
              value={seedText}
              aria-invalid={seed === "invalid"}
              onChange={(event) => setSeedText(event.target.value.trim())}
            />
          </label>
          <BotSpeedSelect delay={botDelay} onChange={setBotDelay} />
        </section>
        <section className="setup-section">
          <label className="setup-checkbox">
            <input
              type="checkbox"
              checked={implementedCardsFirst}
              onChange={(event) => setImplementedCardsFirst(event.target.checked)}
            />
            Deal the implemented cards first
          </label>
          <p className="setup-hint">
            Until every card is implemented, this puts the playable ones on top of the deck. Off, the deck is
            shuffled as the rules say.
          </p>
        </section>
        {seed === "invalid" && (
          <p className="setup-error">
            A seed is a whole number from 0 to {Number.MAX_SAFE_INTEGER}; leave it empty for a random one.
          </p>
        )}
        {error && <p className="setup-error">{error}</p>}

        <div className="setup-buttons">
          {onCancel && (
            <button className="link-button" onClick={onCancel}>
              Back to the Game
            </button>
          )}
          <CardsButton onClick={onShowCards} />
          <LoadReplayButton className="link-button" onLoad={(file) => onLoad(file, botDelay)} />
          <button className="option big" disabled={seed === "invalid"} onClick={start}>
            Start Game
          </button>
        </div>
      </div>
    </main>
  );
}

/** The seed typed in: a number, null when left empty (the server picks one), or invalid. */
function parseSeed(text: string): number | null | "invalid" {
  if (text === "") return null;
  if (!/^\d+$/.test(text)) return "invalid";
  const seed = Number(text);
  return Number.isSafeInteger(seed) ? seed : "invalid";
}

/** What the Controllers chosen mean for what the screen shows. */
function viewHint(controllers: Controller[]): string {
  const humans = controllers.filter((controller) => controller === "human").length;
  if (humans === 0) return "Only Random Bots: you watch, and see everything.";
  if (humans === 1) return "You see only what your Player may know.";
  return "Hotseat: every human plays at this screen, and everything is shown.";
}
