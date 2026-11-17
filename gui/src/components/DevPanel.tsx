import { useEffect, useState } from "react";

import { useCardsById } from "../cards/catalog";
import { PLAYER_COLOURS } from "../players";
import type { Card, DevView, Explanation, Scenario } from "../types";
import { GameLog } from "./GameLog";
import { StateEditor } from "./StateEditor";

interface Props {
  /** The card catalog. */
  cards: Card[];
  /** What the server last showed; null until it answers. */
  shown: DevView | null;
  /** The step asked for, or null for the latest. */
  step: number | null;
  onStep: (step: number | null) => void;
  fullView: boolean;
  onFullView: (on: boolean) => void;
  /** The Player whose Player View the screen shows, or null if it shows the full view anyway. */
  viewer: number | null;
  error: string | null;
  onStartFrom: (scenario: Scenario) => void;
  onClose: () => void;
}

/** A position being edited, and the step it was read from. */
interface Edit {
  scenario: Scenario;
  readFrom: DevView;
}

/** For hunting rule bugs, beside the game view: the seed, Replay step-through, the full-view switch,
 * the state editor and the game log. Only the state editor's Start button changes the Game. The
 * position being edited is kept across its tabs, until it is read again or the Game is replaced. */
export function DevPanel({ cards, shown, step, onStep, fullView, onFullView, viewer, error, onStartFrom, onClose }: Props) {
  const [tab, setTab] = useState<"replay" | "bot" | "editor">("replay");
  const [edit, setEdit] = useState<Edit | null>(null);
  const read = (from: DevView) => setEdit({ scenario: from.scenario, readFrom: from });
  useEffect(() => {
    if (tab === "editor" && edit === null && shown) read(shown);
  }, [tab, edit, shown]);
  // An error stays until the next try, though the next update, a Random Bot's say, clears the Game's.
  const [lastError, setLastError] = useState<string | null>(null);
  useEffect(() => {
    if (error) setLastError(error);
  }, [error]);

  return (
    <aside className="dev-panel" aria-label="Dev panel">
      <header className="dev-panel-header">
        <h2>Dev panel</h2>
        <span className="dev-panel-seed">
          Seed <span className="seed-value">{shown?.seed}</span>
        </span>
        <label className="dev-panel-switch">
          <input type="checkbox" checked={fullView} onChange={(event) => onFullView(event.target.checked)} />
          Full view
        </label>
        <button className="link-button" onClick={onClose}>
          Close
        </button>
      </header>
      <div className="segmented dev-panel-tabs" role="group" aria-label="Dev panel section">
        <button className={tab === "replay" ? "selected" : ""} aria-pressed={tab === "replay"} onClick={() => setTab("replay")}>
          Replay
        </button>
        <button className={tab === "bot" ? "selected" : ""} aria-pressed={tab === "bot"} onClick={() => setTab("bot")}>
          Bot
        </button>
        <button className={tab === "editor" ? "selected" : ""} aria-pressed={tab === "editor"} onClick={() => setTab("editor")}>
          State editor
        </button>
      </div>
      {lastError && <p className="dev-panel-error">{lastError}</p>}
      {shown && shown.position_problems.length > 0 && <PositionProblems problems={shown.position_problems} />}
      {shown && tab === "replay" && (
        <>
          <StepThrough shown={shown} onStep={onStep} step={step} />
          <DecisionAtStep shown={shown} hidden={!fullView && viewer !== null && shown.decision?.player !== viewer} />
          {fullView && <HandsAndDeck shown={shown} cards={cards} />}
          <GameLog log={shown.log} />
        </>
      )}
      {shown && tab === "bot" && (
        <>
          <StepThrough shown={shown} onStep={onStep} step={step} />
          <WhyPicked shown={shown} hidden={!fullView && viewer !== null && shown.decision?.player !== viewer} />
        </>
      )}
      {shown && tab === "editor" && edit && (
        <StateEditor
          cards={cards}
          edited={edit.scenario}
          board={shown.full_view.board}
          readFromStep={edit.readFrom.step}
          underWay={edit.readFrom.decision !== null && edit.readFrom.decision.kind !== "action"}
          onChange={(scenario) => setEdit({ ...edit, scenario })}
          onRead={() => read(shown)}
          onStart={() => {
            setLastError(null);
            onStartFrom(edit.scenario);
          }}
        />
      )}
    </aside>
  );
}

/** Why real play could not reach the position shown: a Scenario may describe it anyway. */
function PositionProblems({ problems }: { problems: string[] }) {
  return (
    <section className="dev-panel-problems">
      <h3>Real play can't reach this position</h3>
      <ul>
        {problems.map((problem) => (
          <li key={problem}>{problem}</li>
        ))}
      </ul>
    </section>
  );
}

interface StepThroughProps {
  shown: DevView;
  step: number | null;
  onStep: (step: number | null) => void;
}

/** Forwards and backwards through the Options picked so far. The latest step follows the Game. */
function StepThrough({ shown, step, onStep }: StepThroughProps) {
  const atStart = shown.step === 0;
  const atLatest = shown.step === shown.steps;
  const goTo = (next: number) => onStep(next >= shown.steps ? null : next);
  return (
    <section className="dev-panel-section">
      <h3>
        Step {shown.step} of {shown.steps} {atLatest ? "(the Game as it is)" : "(looking back)"}
      </h3>
      <input
        className="dev-panel-slider"
        type="range"
        aria-label="Step"
        min={0}
        max={shown.steps}
        value={shown.step}
        onChange={(event) => goTo(Number(event.target.value))}
      />
      <div className="dev-panel-buttons">
        <button className="link-button" disabled={atStart} onClick={() => goTo(0)}>
          First
        </button>
        <button className="link-button" disabled={atStart} onClick={() => goTo(shown.step - 1)}>
          Back
        </button>
        <button className="link-button" disabled={atLatest} onClick={() => goTo(shown.step + 1)}>
          Forward
        </button>
        <button className="link-button" disabled={step === null} onClick={() => onStep(null)}>
          Latest
        </button>
      </div>
    </section>
  );
}

interface DecisionAtStepProps {
  shown: DevView;
  /** Whether the Decision is another Player's, and the full view is off. */
  hidden: boolean;
}

/** The Decision waiting at the step shown, every Option it offers, and the one picked. */
function DecisionAtStep({ shown, hidden }: DecisionAtStepProps) {
  const { decision, picked } = shown;
  if (!decision) return <p className="dev-panel-note">The Game is over at this step.</p>;
  return (
    <section className="dev-panel-section">
      <h3>
        <span className="player-dot" style={{ background: PLAYER_COLOURS[decision.player] }} />{" "}
        {shown.full_view.players[decision.player].name} decides: {decision.kind}
      </h3>
      {hidden ? (
        <p className="dev-panel-note">Switch on the full view to see their Options.</p>
      ) : (
        <ol className="dev-panel-options" start={0}>
          {decision.options.map((option) => (
            <li key={option.index} className={option.index === picked ? "picked" : ""}>
              {option.label}
              {option.index === picked && " ← picked"}
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}

/** How many Options the Bot tab prices at first, before "Show all". */
const TOP_OPTIONS = 5;

interface WhyPickedProps {
  shown: DevView;
  /** Whether the Decision is another Player's, and the full view is off: its Options show their hand. */
  hidden: boolean;
}

/** Why the Controller answering the step shown picks what it picks: its top Options, each with its price
 * and the Prices that changed most. */
function WhyPicked({ shown, hidden }: WhyPickedProps) {
  const [all, setAll] = useState(false);
  const { decision, explanation } = shown;
  if (!decision) return <p className="dev-panel-note">The Game is over at this step.</p>;
  if (!explanation) return <p className="dev-panel-note">No registered Controller that explains its picks answers this step.</p>;
  if (hidden) return <p className="dev-panel-note">Switch on the full view to see why: its Options show its hand.</p>;
  const options = all ? explanation.options : explanation.options.slice(0, TOP_OPTIONS);
  return (
    <section className="dev-panel-section dev-panel-why" aria-label="Why the Controller picks">
      <h3>
        <span className="player-dot" style={{ background: PLAYER_COLOURS[explanation.player] }} /> {explanation.controller},{" "}
        {explanation.kind}
      </h3>
      <p className="dev-panel-note">{generationsLeft(explanation)}</p>
      <ol className="dev-panel-priced">
        {options.map((option) => (
          <li key={option.index} className={option.index === shown.picked ? "picked" : ""}>
            <span className="priced-label">
              {option.label}
              {option.index === shown.picked && " ← picked"}
            </span>
            <span className="priced-value">{signed(option.price)}</span>
            {option.reasons.length > 0 && (
              <span className="priced-reasons">{option.reasons.map(([what, change]) => `${what} ${signed(change)}`).join(", ")}</span>
            )}
          </li>
        ))}
      </ol>
      {explanation.options.length > TOP_OPTIONS && (
        <button className="link-button" onClick={() => setAll(!all)}>
          {all ? `Show the top ${TOP_OPTIONS}` : `Show all ${explanation.options.length}`}
        </button>
      )}
    </section>
  );
}

function generationsLeft(explanation: Explanation): string {
  return `Prices in MegaCredits against doing nothing, with about ${explanation.generations_left.toFixed(1)} Generations left for every Option.`;
}

function signed(value: number): string {
  return `${value >= 0 ? "+" : "−"}${Math.abs(value).toFixed(1)}`;
}

/** Everything hidden at the step shown: all hands, the deck from the top down, and the discard pile. */
function HandsAndDeck({ shown, cards }: { shown: DevView; cards: Card[] }) {
  const catalog = useCardsById(cards);
  const name = (id: string) => catalog.get(id)?.name ?? id;
  const { players, deck, discard } = shown.full_view;
  return (
    <section className="dev-panel-section dev-panel-hidden-cards" aria-label="Hands and deck">
      <h3>Hands</h3>
      {players.map((board, index) => (
        <p key={index}>
          <span className="player-dot" style={{ background: PLAYER_COLOURS[index] }} /> <strong>{board.name}:</strong>{" "}
          {(board.hand ?? []).map(name).join(", ") || "no cards"}
        </p>
      ))}
      <details open>
        <summary>Deck, from the top ({deck?.length ?? 0})</summary>
        <ol className="dev-panel-deck">
          {deck?.map((id) => <li key={id}>{name(id)}</li>)}
        </ol>
      </details>
      <details>
        <summary>Discard pile ({discard?.length ?? 0})</summary>
        <p>{discard?.map(name).join(", ")}</p>
      </details>
    </section>
  );
}
