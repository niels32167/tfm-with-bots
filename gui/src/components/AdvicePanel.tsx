import { controllerLabel } from "../players";
import type { Advice, AdvisedDecision, Card, ControllerName, ControllerOnOffer } from "../types";
import type { GameUpdate } from "../useGameServer";

interface Props {
  game: GameUpdate;
  /** The card catalog, for the names of the cards the bot would choose. */
  cards: Card[];
  /** The Controllers the server offers, for their labels. */
  offered: ControllerOnOffer[];
  /** The bot asked, and its advice once it has thought. */
  bot: ControllerName | null;
  advice: Advice | null;
  onBot: (bot: ControllerName) => void;
  onClose: () => void;
}

// How setup's Decisions are headed, by kind.
const TITLES: Record<string, string> = {
  corporation: "Corporation",
  prelude_cards: "First Prelude Card",
  buy_cards: "First card to buy",
};

/** What a bot would do at the Decision a human is answering, and how it rates the Options, to learn from. */
export function AdvicePanel({ game, cards, offered, bot, advice, onBot, onClose }: Props) {
  return (
    <section className="advice-panel" aria-label="What the bot would do">
      <header className="advice-panel-header">
        <h2>What would the bot do?</h2>
        <button className="link-button" aria-label="Hide the bot's advice" onClick={onClose}>
          ✕
        </button>
      </header>
      {bot === null ? (
        <p className="advice-panel-note">No bot can give advice in this Game.</p>
      ) : (
        <>
          <select aria-label="The bot to ask" value={bot} onChange={(event) => onBot(event.target.value)}>
            {game.advisers.map((name) => (
              <option key={name} value={name}>
                {controllerLabel(offered, name)}
              </option>
            ))}
          </select>
          {advice ? <Advised advice={advice} cards={cards} /> : <p className="advice-panel-note">{waiting(game)}</p>}
        </>
      )}
    </section>
  );
}

function waiting(game: GameUpdate): string {
  return game.decision ? "Thinking…" : "It answers when you have something to decide.";
}

function Advised({ advice, cards }: { advice: Advice; cards: Card[] }) {
  const names = advice.cards.map((id) => cards.find((card) => card.id === id)?.name ?? id);
  const several = advice.decisions.length > 1;
  return (
    <>
      {(several || names.length > 1) && (
        <p className="advice-panel-cards">
          <strong>It would choose</strong> {names.length > 0 ? names.join(", ") : "nothing"}
        </p>
      )}
      {advice.decisions.map((decision) => (
        <OneDecision
          key={decision.kind}
          decision={decision}
          title={several ? (TITLES[decision.kind] ?? null) : null}
        />
      ))}
    </>
  );
}

/** One Decision's Options, best first, with what each measure says of them. */
function OneDecision({ decision, title }: { decision: AdvisedDecision; title: string | null }) {
  return (
    <div className="advice-decision">
      {title && <h3>{title}</h3>}
      <ol>
        {decision.options.map((option) => (
          <li key={option.index} className={option.index === decision.picked ? "picked" : ""}>
            <span className="advice-option">
              {option.index === decision.picked && "★ "}
              {option.label}
            </span>
            {decision.measures.map((measure, index) => {
              const value = option.measured[index];
              if (value === null || value === undefined) return null;
              return (
                <span key={measure.name} className="advice-value">
                  {measure.percent && <span className="advice-bar" style={{ width: `${Math.round(100 * value)}%` }} />}
                  <span>{measure.name}</span>
                  <strong>{measure.percent ? `${Math.round(100 * value)} %` : value.toFixed(1)}</strong>
                </span>
              );
            })}
          </li>
        ))}
      </ol>
      {decision.more > 0 && <p className="advice-panel-note">and {decision.more} more</p>}
    </div>
  );
}
