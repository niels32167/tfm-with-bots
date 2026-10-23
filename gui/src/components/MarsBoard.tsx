import type { KeyboardEvent, ReactNode } from "react";

import { TILE_NAMES } from "../format";
import { PLAYER_COLOURS } from "../players";
import type { Area, BonusItem, Decision, DecisionOption, Tile } from "../types";
import { OxygenTrack } from "./OxygenTrack";

// Areas are hexagons with a corner at the top. SIZE is the distance from the centre of
// an Area to its corners, in the SVG's own units.
const SIZE = 30;
const WIDTH = Math.sqrt(3) * SIZE;
const ROW_HEIGHT = 1.5 * SIZE;
const WIDEST_ROW = 9;
const MIDDLE_ROW = 5;
const GLOBE_RADIUS = 8.2 * SIZE;
// The Oxygen track runs round the globe, with room for it inside the view.
const OXYGEN_TRACK_RADIUS = GLOBE_RADIUS + 22;
const VIEW_RADIUS = OXYGEN_TRACK_RADIUS + 20;

const HEXAGON = [30, 90, 150, 210, 270, 330]
  .map((degrees) => {
    const angle = (degrees * Math.PI) / 180;
    return `${(SIZE * Math.cos(angle)).toFixed(2)},${(SIZE * Math.sin(angle)).toFixed(2)}`;
  })
  .join(" ");


interface Props {
  board: Area[];
  /** In percent, for the Oxygen track. */
  oxygen: number;
  /** Each Player's name, by index, for the tooltips. */
  playerNames: string[];
  /** The Decision a human at the screen must answer, if any. Its Areas are highlighted and clickable. */
  decision: Decision | null;
  /** True while a pick is on its way to the server. */
  disabled: boolean;
  onPick: (sequence: number, index: number) => void;
}

/** Mars with every Area, its placement bonus and its Tile, as on the Tharsis board, and the Oxygen track round it. */
export function MarsBoard({ board, oxygen, playerNames, decision, disabled, onPick }: Props) {
  const options = areaOptions(decision);
  const rowLengths = new Map<number, number>();
  for (const area of board) {
    if (area.row !== null) rowLengths.set(area.row, (rowLengths.get(area.row) ?? 0) + 1);
  }
  const firstOffMars = board.findIndex((area) => area.row === null);
  const pick = (option: DecisionOption) => {
    if (decision && !disabled) onPick(decision.sequence, option.index);
  };

  return (
    <svg
      className={`mars-board ${options.size > 0 ? "choosing" : ""}`}
      viewBox={`${-VIEW_RADIUS} ${-VIEW_RADIUS} ${2 * VIEW_RADIUS} ${2 * VIEW_RADIUS}`}
      role="group"
      aria-label="Mars"
    >
      <defs>
        <radialGradient id="mars-globe" cx="38%" cy="32%" r="75%">
          <stop offset="0%" stopColor="#e89366" />
          <stop offset="30%" stopColor="#c45c36" />
          <stop offset="65%" stopColor="#8a3420" />
          <stop offset="100%" stopColor="#3a120a" />
        </radialGradient>
      </defs>
      <circle className="mars-globe" r={GLOBE_RADIUS} fill="url(#mars-globe)" />
      <OxygenTrack oxygen={oxygen} radius={OXYGEN_TRACK_RADIUS} />
      {board.map((area, index) => {
        const [x, y] =
          area.row !== null && area.position !== null
            ? centreOnMars(area.row, area.position, rowLengths.get(area.row) ?? WIDEST_ROW)
            : centreOffMars(index - firstOffMars);
        return (
          <AreaMark
            key={area.area}
            area={area}
            x={x}
            y={y}
            offMars={area.row === null}
            ownerName={area.tile?.owner != null ? playerNames[area.tile.owner] : null}
            option={options.get(area.area)}
            onPick={pick}
          />
        );
      })}
    </svg>
  );
}

/** The Options of a choose-an-Area Decision, by the Area they name. */
function areaOptions(decision: Decision | null): Map<string, DecisionOption> {
  const options = new Map<string, DecisionOption>();
  for (const option of decision?.options ?? []) {
    if (option.details.type === "area") options.set(option.details.area as string, option);
  }
  return options;
}

/** Each row is centred under the widest one, so neighbours in the next row sit half an Area to either side. */
function centreOnMars(row: number, position: number, rowLength: number): [number, number] {
  const halfColumn = 2 * (position - 1) + (WIDEST_ROW - rowLength);
  return [((halfColumn - (WIDEST_ROW - 1)) * WIDTH) / 2, (row - MIDDLE_ROW) * ROW_HEIGHT];
}

/** The Areas off Mars sit in the bottom corners, away from the globe and the Oxygen track. */
function centreOffMars(index: number): [number, number] {
  const corner = GLOBE_RADIUS * 0.86;
  return [index === 0 ? -corner : corner, corner];
}

interface AreaMarkProps {
  area: Area;
  x: number;
  y: number;
  offMars: boolean;
  /** The name of the Player who owns its Tile, if anyone does. */
  ownerName: string | null;
  option: DecisionOption | undefined;
  onPick: (option: DecisionOption) => void;
}

function AreaMark({ area, x, y, offMars, ownerName, option, onPick }: AreaMarkProps) {
  const classes = [
    "area",
    offMars ? "off-mars" : "",
    area.reserved ? `reserved-${area.reserved === "ocean" ? "ocean" : "card"}` : "",
    area.tile ? `tile tile-${area.tile.type}` : "",
    option ? "choosable" : "",
  ];
  const interactive = option
    ? {
        role: "button",
        tabIndex: 0,
        "aria-label": option.label,
        onClick: () => onPick(option),
        onKeyDown: (event: KeyboardEvent) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            onPick(option);
          }
        },
      }
    : {};
  return (
    <g className={classes.join(" ")} transform={`translate(${x.toFixed(2)} ${y.toFixed(2)})`} {...interactive}>
      <title>{describe(area, ownerName)}</title>
      {offMars ? <circle className="area-shape" r={SIZE * 0.8} /> : <polygon className="area-shape" points={HEXAGON} />}
      {area.tile ? <TileMark tile={area.tile} /> : <BonusMarks bonus={area.bonus} />}
      {area.name && (
        <text className="area-name" y={offMars ? SIZE * 1.25 : -SIZE * 0.5}>
          {area.name}
        </text>
      )}
      {!offMars && (
        <text className="area-id" y={SIZE * 0.78}>
          {area.area}
        </text>
      )}
    </g>
  );
}

/** A Tile: its colour shows its type, and a disc in its owner's colour shows whose it is. */
function TileMark({ tile }: { tile: Tile }) {
  return (
    <g className="tile-mark">
      {tile.type === "city" && <path className="city-skyline" d="M-11,2 v-9 h5 v-5 h6 v8 h5 v-4 h6 v10 z" />}
      {tile.owner !== null && (
        <circle className="owner-marker" cy={tile.type === "city" ? 8 : 0} r={7} fill={PLAYER_COLOURS[tile.owner]} />
      )}
    </g>
  );
}

/** The placement bonus, one small mark per item, side by side. */
function BonusMarks({ bonus }: { bonus: BonusItem[] }) {
  const spacing = 15;
  const left = (-(bonus.length - 1) * spacing) / 2;
  return (
    <g className="bonus">
      {bonus.map((item, index) => (
        <g key={index} transform={`translate(${left + index * spacing} 0)`}>
          {BONUS_MARKS[item]}
        </g>
      ))}
    </g>
  );
}

const BONUS_MARKS: Record<BonusItem, ReactNode> = {
  steel: (
    <>
      <rect className="bonus-steel" x={-6} y={-6} width={12} height={12} rx={2} />
      <text className="bonus-letter">S</text>
    </>
  ),
  titanium: (
    <>
      <polygon className="bonus-titanium" points="0,-7 6.5,0 0,7 -6.5,0" />
      <text className="bonus-letter">T</text>
    </>
  ),
  plant: <path className="bonus-plant" d="M0,7 C-8,2 -6,-6 0,-7 C6,-6 8,2 0,7 Z" />,
  card: <rect className="bonus-card" x={-5} y={-7} width={10} height={14} rx={1.5} />,
};

/** The tooltip: everything about an Area in words. */
function describe(area: Area, ownerName: string | null): string {
  const lines = [area.name ? `${area.area}: ${area.name}` : area.area];
  if (area.reserved === "ocean") lines.push("Reserved for Oceans");
  else if (area.reserved) lines.push(`Reserved for the ${area.name} card`);
  if (area.bonus.length > 0) lines.push(`Placement bonus: ${countBonus(area.bonus)}`);
  if (area.tile) lines.push(`${TILE_NAMES[area.tile.type]}${ownerName ? ` of ${ownerName}` : ""}`);
  return lines.join("\n");
}

/** "2 plants", "1 steel and 1 titanium". */
function countBonus(bonus: BonusItem[]): string {
  const counts = new Map<BonusItem, number>();
  for (const item of bonus) counts.set(item, (counts.get(item) ?? 0) + 1);
  return [...counts]
    .map(([item, count]) => {
      const plural = count > 1 && (item === "plant" || item === "card") ? "s" : "";
      return `${count} ${item}${plural}`;
    })
    .join(" and ");
}
