import { useState } from "react";

import { CardsButton } from "../cards/CardsButton";
import { PLAYER_COLOURS } from "../players";
import { type ControllerName, type ControllerOnOffer, HUMAN, type NewGameSettings } from "../types";
import { BotSpeedSelect } from "./BotSpeedSelect";
import { LoadReplayButton } from "./LoadReplayButton";

const PLAYER_COUNTS = [2, 3, 4, 5];
const MAX_PLAYERS = Math.max(...PLAYER_COUNTS);

interface Props {
  /** The Controllers to choose from for each Player, as the server offers them. */
  offered: ControllerOnOffer[];
  /** Controllers and bot delay to start from, say those of the Game being replaced. */
  initialControllers: ControllerName[];
  initialBotDelay: number;
  error: string | null;
  onStart: (settings: NewGameSettings) => void;
  onLoad: (file: File, botDelay: number) => void;
  onShowCards: () => void;
  /** Leaves the setup screen without starting anything; absent when there is no Game to go back to. */
  onCancel?: () => void;
}

/** The intro and new-Game screen: Players and who controls each, whether the Research phases have the Draft and the Game
 * Prelude, the seed and how fast bots pick. */
export function NewGameSetup({
  offered,
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
  const [allControllers, setAllControllers] = useState<ControllerName[]>(() =>
    Array.from({ length: MAX_PLAYERS }, (_, player) => initialControllers[player] ?? "random_bot"),
  );
  const [seedText, setSeedText] = useState("");
  const [botDelay, setBotDelay] = useState(initialBotDelay);
  const [draft, setDraft] = useState(true);
  // On by default, as the AI is trained and plays with Prelude (ADR 0011).
  const [prelude, setPrelude] = useState(true);

  const controllers = allControllers.slice(0, playerCount);
  const seed = parseSeed(seedText);
  const cantPlay = controllers
    .map((name) => offered.find((candidate) => candidate.name === name))
    .find((candidate) => candidate !== undefined && candidate.most_players < playerCount);

  const setController = (player: number, controller: ControllerName) =>
    setAllControllers((previous) => previous.map((old, index) => (index === player ? controller : old)));

  const start = () => {
    if (seed === "invalid") return;
    onStart({
      controllers,
      bot_delay: botDelay,
      draft,
      prelude,
      ...(seed === null ? {} : { seed }),
    });
  };

  return (
    <main className="intro">
      <div className="intro-planet" aria-hidden />
      <header className="intro-title">
        <h1>
          <span>Terraforming</span> Mars
        </h1>
        <p>
          Warm the planet, make its air breathable and fill its oceans. Lead a Corporation, and outdo your rivals by the
          time Mars is a world to live on.
        </p>
      </header>

      <div className="setup">
        <h2 className="setup-title">New Game</h2>

        <section className="setup-section" aria-labelledby="setup-players">
          <div className="setup-row">
            <h3 id="setup-players">Players</h3>
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
          </div>
          <ol className="setup-players">
            {controllers.map((controller, player) => (
              <li key={player} className="setup-player" style={{ borderLeftColor: PLAYER_COLOURS[player] }}>
                <label htmlFor={`controller-${player}`}>Player {player + 1}</label>
                <select
                  id={`controller-${player}`}
                  value={controller}
                  onChange={(event) => setController(player, event.target.value)}
                >
                  <ControllerOptions offered={offered} chosen={controller} players={playerCount} />
                </select>
                <p className="setup-hint">{offered.find((candidate) => candidate.name === controller)?.description}</p>
              </li>
            ))}
          </ol>
          {cantPlay ? (
            <p className="setup-error">
              The {cantPlay.label} plays only in {cantPlay.most_players}-Player Games.
            </p>
          ) : (
            <p className="setup-hint">{viewHint(controllers)}</p>
          )}
        </section>

        <section className="setup-section setup-switches">
          <label className="setup-checkbox">
            <input type="checkbox" checked={prelude} onChange={(event) => setPrelude(event.target.checked)} />
            <span>
              Prelude
              <small>Keep 2 of 4 Prelude Cards at setup for a faster start, and play with Prelude's cards.</small>
            </span>
          </label>
          <label className="setup-checkbox">
            <input type="checkbox" checked={draft} onChange={(event) => setDraft(event.target.checked)} />
            <span>
              Draft
              <small>From Generation 2, pick cards one at a time from hands passed around.</small>
            </span>
          </label>
        </section>

        <details className="setup-more">
          <summary>More options</summary>
          <div className="setup-row">
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
          </div>
          {seed === "invalid" && (
            <p className="setup-error">
              A seed is a whole number from 0 to {Number.MAX_SAFE_INTEGER}; leave it empty for a random one.
            </p>
          )}
        </details>
        {error && <p className="setup-error">{error}</p>}

        <button className="option setup-start" disabled={seed === "invalid" || cantPlay !== undefined} onClick={start}>
          Start Game
        </button>
        <div className="setup-buttons">
          {onCancel && (
            <button className="link-button" onClick={onCancel}>
              Back to the Game
            </button>
          )}
          <CardsButton onClick={onShowCards} />
          <LoadReplayButton className="link-button" onLoad={(file) => onLoad(file, botDelay)} />
        </div>
      </div>
    </main>
  );
}

interface ControllerOptionsProps {
  offered: ControllerOnOffer[];
  chosen: ControllerName;
  players: number;
}

/** The Controllers to choose from in a drop-down: a human, then the bots as the server lists them.
 * Those that don't play in Games of this many `players` can't be chosen. */
function ControllerOptions({ offered, chosen, players }: ControllerOptionsProps) {
  const option = ({ name, label, most_players: most }: ControllerOnOffer) => (
    <option key={name} value={name} disabled={most < players}>
      {most < players ? `${label} (${most} Players only)` : label}
    </option>
  );
  const known = offered.some((candidate) => candidate.name === chosen);
  return (
    <>
      {offered.filter(({ name }) => name === HUMAN).map(option)}
      <optgroup label="Bots">{offered.filter(({ name }) => name !== HUMAN).map(option)}</optgroup>
      {/* A Controller with settings, as a Replay file may name one. */}
      {!known && <option value={chosen}>{chosen}</option>}
    </>
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
function viewHint(controllers: ControllerName[]): string {
  const humans = controllers.filter((controller) => controller === HUMAN).length;
  if (humans === 0) return "No human: you watch, and see everything.";
  if (humans === 1) return "You see only what your Player may know.";
  return "Hotseat: every human plays at this screen, and everything is shown.";
}
