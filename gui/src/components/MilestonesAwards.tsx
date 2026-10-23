import type { ReactNode } from "react";

import { formatNumber } from "../format";
import { PLAYER_COLOURS, playerTitle } from "../players";
import type { Decision, DecisionOption } from "../types";
import type { GameUpdate } from "../useGameServer";

// How many Milestones can be claimed, and how many Awards funded, per Game (printed on the board).
const PER_GAME = 3;

interface Props {
  game: GameUpdate;
  /** True while a pick is on its way to the server. */
  disabled: boolean;
  onPick: (sequence: number, index: number) => void;
}

/** The Milestones and Awards bar under Mars: prices, who claimed or funded what, and where
 * each Player stands. A Milestone or Award the current Decision offers is highlighted and clicked here. */
export function MilestonesAwards({ game, disabled, onPick }: Props) {
  const { view, decision } = game;
  const claimable = offeredBy(decision, "claim_milestone", "milestone");
  const fundable = offeredBy(decision, "fund_award", "award");
  const pick = (option: DecisionOption) => {
    if (decision && !disabled) onPick(decision.sequence, option.index);
  };
  const claimedCount = view.milestones.filter((milestone) => milestone.claimed_by !== null).length;
  const fundedCount = view.awards.filter((award) => award.funded_by !== null).length;

  return (
    <section className="milestones-awards" aria-label="Milestones and Awards">
      <Group
        title="Milestones"
        price={
          view.milestone_cost === null
            ? `${PER_GAME} of ${PER_GAME} claimed`
            : `${view.milestone_cost} MegaCredits · ${claimedCount} of ${PER_GAME} claimed`
        }
      >
        {view.milestones.map((milestone) => (
          <Entry
            key={milestone.milestone}
            game={game}
            name={milestone.name}
            condition={milestone.condition}
            counts={milestone.counts}
            target={milestone.target}
            takenBy={milestone.claimed_by}
            taken="claimed"
            option={claimable.get(milestone.milestone)}
            disabled={disabled}
            onPick={pick}
          />
        ))}
      </Group>
      <Group
        title="Awards"
        price={
          view.award_cost === null
            ? `${PER_GAME} of ${PER_GAME} funded`
            : `next ${view.award_cost} MegaCredits · ${fundedCount} of ${PER_GAME} funded`
        }
      >
        {view.awards.map((award) => (
          <Entry
            key={award.award}
            game={game}
            name={award.name}
            condition={award.condition}
            counts={award.counts}
            takenBy={award.funded_by}
            taken="funded"
            option={fundable.get(award.award)}
            disabled={disabled}
            onPick={pick}
          />
        ))}
      </Group>
    </section>
  );
}

function Group({ title, price, children }: { title: string; price: string; children: ReactNode }) {
  return (
    <div className="milestones-awards-group">
      <h2>
        {title} <span className="milestones-awards-price">{price}</span>
      </h2>
      <div className="milestones-awards-entries">{children}</div>
    </div>
  );
}

interface EntryProps {
  game: GameUpdate;
  name: string;
  condition: string;
  counts: number[];
  /** A Milestone's target, shown until it is claimed. */
  target?: number;
  takenBy: number | null;
  taken: "claimed" | "funded";
  /** The Option that claims or funds it, if the current Decision offers one. */
  option: DecisionOption | undefined;
  disabled: boolean;
  onPick: (option: DecisionOption) => void;
}

function Entry({ game, name, condition, counts, target, takenBy, taken, option, disabled, onPick }: EntryProps) {
  const standings = counts
    .map((count, player) => `${game.view.players[player].name}: ${formatNumber(count)}`)
    .join(" · ");
  const takenText = takenBy === null ? "" : `\n${taken === "claimed" ? "Claimed" : "Funded"} by ${playerTitle(game, takenBy)}`;
  const content = (
    <>
      <span className="milestones-awards-name">{name}</span>
      <span className="milestones-awards-counts">
        {counts.map((count, player) => (
          <span key={player} className="milestones-awards-count" style={{ color: PLAYER_COLOURS[player] }}>
            {formatNumber(count)}
          </span>
        ))}
      </span>
      {takenBy !== null ? (
        <span className="milestones-awards-taken">
          <span className="player-dot" style={{ background: PLAYER_COLOURS[takenBy] }} />
          {playerTitle(game, takenBy)}
        </span>
      ) : (
        target !== undefined && <span className="milestones-awards-needs">needs {target}</span>
      )}
    </>
  );
  const className = `milestones-awards-entry ${takenBy !== null ? "taken" : ""}`;
  const style = takenBy !== null ? { borderColor: PLAYER_COLOURS[takenBy] } : undefined;
  const title = `${name}: ${condition}\n${standings}${takenText}`;
  if (option) {
    return (
      <button
        className={`${className} offered`}
        style={style}
        title={`${title}\n${option.label}`}
        aria-label={option.label}
        disabled={disabled}
        onClick={() => onPick(option)}
      >
        {content}
      </button>
    );
  }
  return (
    <div className={className} style={style} title={title}>
      {content}
    </div>
  );
}

/** The current Decision's Options of `type`, by the id their details name under `key`. */
function offeredBy(decision: Decision | null, type: string, key: string): Map<string, DecisionOption> {
  const found = new Map<string, DecisionOption>();
  for (const option of decision?.options ?? []) {
    if (option.details.type === type) found.set(option.details[key] as string, option);
  }
  return found;
}
