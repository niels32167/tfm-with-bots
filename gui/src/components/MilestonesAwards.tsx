import type { ReactNode } from "react";

import { formatNumber } from "../format";
import { PLAYER_COLOURS, playerTitle } from "../players";
import { AWARD_PRICES, MILESTONE_PRICES } from "../tracks";
import type { Decision, DecisionOption } from "../types";
import type { GameUpdate } from "../useGameServer";
import { PlayerCube, svgButton } from "./boardLayout";

const PANEL_Y = 542;
const PANEL_WIDTH = 374;
const PANEL_HEIGHT = 94;
const ENTRY_TOP = 24;
const ENTRY_WIDTH = 71;
const ENTRY_HEIGHT = 65;
const ENTRY_GAP = 2;

interface Props {
  game: GameUpdate;
  /** True while a pick is on its way to the server. */
  disabled: boolean;
  onPick: (sequence: number, index: number) => void;
}

/** The two silver panels along the bottom of the board: the prices, with those used crossed out, who
 * claimed or funded what, and where each Player stands. What the current Decision offers is lit and
 * clicked here. */
export function MilestonesAwards({ game, disabled, onPick }: Props) {
  const { view, decision } = game;
  const claimable = offeredBy(decision, "claim_milestone", "milestone");
  const fundable = offeredBy(decision, "fund_award", "award");
  const pick = (option: DecisionOption) => {
    if (decision && !disabled) onPick(decision.sequence, option.index);
  };
  const claimed = view.milestones.filter((milestone) => milestone.claimed_by !== null).length;
  const funded = view.awards.filter((award) => award.funded_by !== null).length;

  return (
    <g className="milestones-awards" role="group" aria-label="Milestones and Awards">
      <Panel
        x={6}
        title="Milestones"
        prices={MILESTONE_PRICES}
        used={claimed}
        priceNote={`${claimed} of ${MILESTONE_PRICES.length} claimed`}
      >
        {view.milestones.map((milestone, position) => (
          <Entry
            key={milestone.milestone}
            position={position}
            game={game}
            name={milestone.name}
            condition={milestone.condition}
            counts={milestone.counts}
            target={milestone.target}
            takenBy={milestone.claimed_by}
            taken="claimed"
            option={claimable.get(milestone.milestone)}
            onPick={pick}
          />
        ))}
      </Panel>
      <Panel
        x={390}
        title="Awards"
        prices={AWARD_PRICES}
        used={funded}
        priceNote={`${funded} of ${AWARD_PRICES.length} funded`}
      >
        {view.awards.map((award, position) => (
          <Entry
            key={award.award}
            position={position}
            game={game}
            name={award.name}
            condition={award.condition}
            counts={award.counts}
            takenBy={award.funded_by}
            taken="funded"
            option={fundable.get(award.award)}
            onPick={pick}
          />
        ))}
      </Panel>
    </g>
  );
}

interface PanelProps {
  x: number;
  title: string;
  /** The prices printed on it, in MegaCredits. */
  prices: readonly number[];
  /** How many of them are used. */
  used: number;
  priceNote: string;
  children: ReactNode;
}

function Panel({ x, title, prices, used, priceNote, children }: PanelProps) {
  const middle = PANEL_WIDTH / 2;
  return (
    <g transform={`translate(${x} ${PANEL_Y})`}>
      <path
        className="milestones-awards-panel"
        d={`M 0 ${PANEL_HEIGHT} V 10 Q 0 0 10 0 H ${PANEL_WIDTH - 10} Q ${PANEL_WIDTH} 0 ${PANEL_WIDTH} 10 V ${PANEL_HEIGHT} Z`}
        fill="url(#silver-panel)"
      />
      <g className="milestones-awards-prices">
        <title>{priceNote}</title>
        {prices.map((price, index) => (
          <g key={index} className={index < used ? "used" : ""} transform={`translate(${14 + index * 20} 12)`}>
            <rect className="price-token" x={-9} y={-9} width={18} height={18} rx={4} />
            <text className="price-token-text small">{price}</text>
            {index < used && <path className="price-used" d="M-7,-7 L7,7 M7,-7 L-7,7" />}
          </g>
        ))}
      </g>
      <rect className="milestones-awards-plate" x={middle - 56} y={3} width={112} height={18} rx={4} fill="url(#gold-plate)" />
      <text className="milestones-awards-title" x={middle} y={12.5}>
        {title}
      </text>
      {children}
    </g>
  );
}

interface EntryProps {
  position: number;
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
  onPick: (option: DecisionOption) => void;
}

function Entry({ position, game, name, condition, counts, target, takenBy, taken, option, onPick }: EntryProps) {
  const standings = counts
    .map((count, player) => `${game.view.players[player].name}: ${formatNumber(count)}`)
    .join(" · ");
  const takenText = takenBy === null ? "" : `\n${taken === "claimed" ? "Claimed" : "Funded"} by ${playerTitle(game, takenBy)}`;
  const tooltip = `${name}: ${condition}\n${standings}${takenText}${option ? `\n${option.label}` : ""}`;
  const chipWidth = Math.min(22, (ENTRY_WIDTH - 6) / counts.length - 1);
  const chipsLeft = (ENTRY_WIDTH - counts.length * (chipWidth + 1)) / 2;
  const middle = ENTRY_WIDTH / 2;
  return (
    <g
      className={`milestones-awards-entry ${takenBy !== null ? "taken" : ""} ${option ? "offered" : ""}`}
      transform={`translate(${6 + position * (ENTRY_WIDTH + ENTRY_GAP)} ${ENTRY_TOP})`}
      {...(option ? svgButton(option.label, () => onPick(option)) : {})}
    >
      <title>{tooltip}</title>
      <rect
        className="milestones-awards-entry-box"
        width={ENTRY_WIDTH}
        height={ENTRY_HEIGHT}
        rx={5}
        style={takenBy !== null ? { stroke: PLAYER_COLOURS[takenBy] } : undefined}
      />
      <text className="milestones-awards-name" x={middle} y={11}>
        {name}
      </text>
      {counts.map((count, player) => (
        <g key={player} transform={`translate(${chipsLeft + player * (chipWidth + 1)} 21)`}>
          <rect className="standing-chip" width={chipWidth} height={14} rx={3} fill={PLAYER_COLOURS[player]} />
          <text className="standing-chip-text" x={chipWidth / 2} y={7.5}>
            {formatNumber(count)}
          </text>
        </g>
      ))}
      {takenBy !== null ? (
        <>
          <PlayerCube colour={PLAYER_COLOURS[takenBy]} x={10} y={49} size={6} />
          <text className="milestones-awards-taken" x={19} y={49}>
            {playerTitle(game, takenBy)}
          </text>
        </>
      ) : (
        target !== undefined && (
          <text className="milestones-awards-needs" x={middle} y={49}>
            needs {target}
          </text>
        )
      )}
    </g>
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
