import type { ReactNode } from "react";

import { TILE_NAMES } from "../format";
import { PLAYER_COLOURS } from "../players";
import type { Area, BonusItem, Card, Decision, DecisionOption, Tile } from "../types";
import type { GameUpdate } from "../useGameServer";
import { BOARD_HEIGHT, BOARD_WIDTH, BoardIcon, GLOBE_RADIUS, GLOBE_X, GLOBE_Y, hexagonPoints, PlayerCube, svgButton } from "./boardLayout";
import { MilestonesAwards } from "./MilestonesAwards";
import { OceanTrack } from "./OceanTrack";
import { OxygenTrack } from "./OxygenTrack";
import { StandardProjects } from "./StandardProjects";
import { TemperatureTrack } from "./TemperatureTrack";

// Areas are hexagons with a corner at the top. SIZE is the distance from the centre of
// an Area to its corners, in the board's own units.
const SIZE = 31;
const WIDTH = Math.sqrt(3) * SIZE;
const ROW_HEIGHT = 1.5 * SIZE;
const WIDEST_ROW = 9;
const MIDDLE_ROW = 5;
const HEXAGON = hexagonPoints(SIZE);
// Where the Areas off Mars sit, from the globe's centre, in the board's order.
const OFF_MARS: [number, number][] = [
  [-288, -226],
  [-296, -68],
];
const OFF_MARS_RADIUS = 34;
// Phobos Space Haven is a rock.
const ASTEROID = "-30,-8 -22,-26 -4,-33 16,-28 31,-14 34,6 22,26 2,32 -18,28 -32,12";

// The symbol drawn on each special Tile, by its card's id, after the card's own art where it has
// one. Capital's City gets a star over its skyline. Ecological Zone's paw is drawn: see `Paw`.
const SPECIAL_SYMBOLS: Record<string, string> = {
  capital: "★",
  natural_preserve: "✿",
  mining_area: "⚒",
  mining_rights: "⚒",
  commercial_district: "€",
  nuclear_zone: "☢",
  industrial_center: "⚙",
  lava_flows: "▲",
  mohole_area: "♨",
  restricted_area: "⊘",
};

// The places printed on the globe: their name, where from its centre, and their angle.
const PLACE_NAMES: [string, number, number, number][] = [
  ["TEMPE TERRA", 25, -196, 0],
  ["LUNAE PLANUM", 80, -101, 0],
  ["SINAI PLANUM", -34, 61, 0],
  ["SOLIS PLANUM", -14, 143, 0],
  ["SYRIA PLANUM", -166, 88, 62],
  ["THAUMASIA FOSSAE", -96, 186, 36],
  ["AONIA TERRA", 148, 160, -38],
];

interface Props {
  game: GameUpdate;
  /** The card catalog, for the names of special Tiles. */
  cards: Card[];
  /** True while a pick is on its way to the server. */
  disabled: boolean;
  onPick: (sequence: number, index: number) => void;
}

/** The board, one picture as on Board Game Arena: Mars on a NASA image with every Area, its placement
 * bonus and its Tile, the Oxygen arc over it, the thermometer and Ocean counter to its right, the
 * Standard Projects to its left, and the Milestones and Awards along the bottom. */
export function MarsBoard({ game, cards, disabled, onPick }: Props) {
  const { view, decision } = game;
  const { board } = view;
  const playerNames = view.players.map((player) => player.name);
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
      viewBox={`0 0 ${BOARD_WIDTH} ${BOARD_HEIGHT}`}
      role="group"
      aria-label="Mars"
    >
      <BoardDefinitions />
      <g className="deck-counts">
        <text x={8} y={12}>
          Draw {view.deck_size} · Discard {view.discard_size}
        </text>
      </g>
      <circle className="mars-glow" cx={GLOBE_X} cy={GLOBE_Y} r={GLOBE_RADIUS + 2} />
      <image
        className="mars-globe"
        href="/mars/mars-valles-marineris.jpeg"
        x={GLOBE_X - GLOBE_RADIUS}
        y={GLOBE_Y - GLOBE_RADIUS}
        width={2 * GLOBE_RADIUS}
        height={2 * GLOBE_RADIUS}
        clipPath="url(#mars-clip)"
      />
      <OxygenTrack oxygen={view.oxygen} />
      <TemperatureTrack temperature={view.temperature} />
      <OceanTrack oceans={view.oceans} />
      <GenerationMark generation={view.generation} />
      <g transform={`translate(${GLOBE_X} ${GLOBE_Y})`}>
        {PLACE_NAMES.map(([name, x, y, angle]) => (
          <text key={name} className="place-name" transform={`translate(${x} ${y}) rotate(${angle})`}>
            {name}
          </text>
        ))}
        {board.map((area, index) => {
          const [x, y] =
            area.row !== null && area.position !== null
              ? centreOnMars(area.row, area.position, rowLengths.get(area.row) ?? WIDEST_ROW)
              : OFF_MARS[index - firstOffMars];
          return (
            <AreaMark
              key={area.area}
              area={area}
              x={x}
              y={y}
              offMars={area.row === null}
              ownerName={area.tile?.owner != null ? playerNames[area.tile.owner] : null}
              claimantName={area.claimed_by !== null ? playerNames[area.claimed_by] : null}
              specialName={cards.find((card) => card.id === area.tile?.card)?.name ?? null}
              option={options.get(area.area)}
              onPick={pick}
            />
          );
        })}
      </g>
      <StandardProjects decision={decision} disabled={disabled} onPick={onPick} />
      <MilestonesAwards game={game} disabled={disabled} onPick={onPick} />
    </svg>
  );
}

/** The colours the board's parts share. */
function BoardDefinitions() {
  return (
    <defs>
      <clipPath id="mars-clip">
        <circle cx={GLOBE_X} cy={GLOBE_Y} r={GLOBE_RADIUS} />
      </clipPath>
      <linearGradient id="tile-ocean" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stopColor="#2f7fd6" />
        <stop offset="100%" stopColor="#134a94" />
      </linearGradient>
      <linearGradient id="tile-greenery" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stopColor="#7cab3f" />
        <stop offset="100%" stopColor="#47701f" />
      </linearGradient>
      <linearGradient id="tile-city" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stopColor="#a4a7ad" />
        <stop offset="100%" stopColor="#6b6e75" />
      </linearGradient>
      <linearGradient id="tile-special" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stopColor="#a56f3f" />
        <stop offset="100%" stopColor="#6d4524" />
      </linearGradient>
      <linearGradient id="oxygen-band" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0%" stopColor="#6d6455" />
        <stop offset="50%" stopColor="#a89c86" />
        <stop offset="100%" stopColor="#6d6455" />
      </linearGradient>
      <linearGradient id="thermometer-mercury" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stopColor="#e8341c" />
        <stop offset="45%" stopColor="#a02a8c" />
        <stop offset="100%" stopColor="#2b5fd0" />
      </linearGradient>
      <radialGradient id="thermometer-bulb" cx="40%" cy="35%" r="75%">
        <stop offset="0%" stopColor="#7cc4ff" />
        <stop offset="100%" stopColor="#1a58c4" />
      </radialGradient>
      <linearGradient id="silver-panel" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stopColor="#eceff1" />
        <stop offset="60%" stopColor="#c3c8cd" />
        <stop offset="100%" stopColor="#9aa0a6" />
      </linearGradient>
      <linearGradient id="gold-plate" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stopColor="#f6d27a" />
        <stop offset="100%" stopColor="#c98f22" />
      </linearGradient>
    </defs>
  );
}

/** The Generation in a ringed circle, above the thermometer. */
function GenerationMark({ generation }: { generation: number }) {
  return (
    <g className="generation-mark" transform="translate(726 36)" role="img" aria-label={`Generation ${generation}`}>
      <circle r={20} />
      <text>{generation}</text>
      <text className="generation-mark-label" y={29}>
        Generation
      </text>
    </g>
  );
}

/** The Options of a choose-an-Area Decision, for a Tile or for Land Claim, by the Area they name. */
function areaOptions(decision: Decision | null): Map<string, DecisionOption> {
  const options = new Map<string, DecisionOption>();
  for (const option of decision?.options ?? []) {
    const { type, area } = option.details;
    if (type === "area" || type === "claim_area") options.set(area as string, option);
  }
  return options;
}

/** Each row is centred under the widest one, so neighbours in the next row sit half an Area to either side. */
function centreOnMars(row: number, position: number, rowLength: number): [number, number] {
  const halfColumn = 2 * (position - 1) + (WIDEST_ROW - rowLength);
  return [((halfColumn - (WIDEST_ROW - 1)) * WIDTH) / 2, (row - MIDDLE_ROW) * ROW_HEIGHT];
}

interface AreaMarkProps {
  area: Area;
  x: number;
  y: number;
  offMars: boolean;
  /** The name of the Player who owns its Tile, if anyone does. */
  ownerName: string | null;
  /** The name of the Player who claimed it with Land Claim, if anyone did. */
  claimantName: string | null;
  /** The name of the card whose symbol its special Tile is printed with, if it has one. */
  specialName: string | null;
  option: DecisionOption | undefined;
  onPick: (option: DecisionOption) => void;
}

function AreaMark({ area, x, y, offMars, ownerName, claimantName, specialName, option, onPick }: AreaMarkProps) {
  const classes = [
    "area",
    offMars ? `off-mars ${area.area}` : "",
    area.reserved ? `reserved-${area.reserved === "ocean" ? "ocean" : "card"}` : "",
    area.tile ? `tile tile-${area.tile.type}` : "",
    option ? "choosable" : "",
  ];
  const interactive = option ? svgButton(option.label, () => onPick(option)) : {};
  const fill = area.tile ? `url(#tile-${area.tile.type})` : undefined;
  return (
    <g className={classes.join(" ")} transform={`translate(${x.toFixed(2)} ${y.toFixed(2)})`} {...interactive}>
      <title>{describe(area, ownerName, claimantName, specialName)}</title>
      {!offMars ? (
        <polygon className="area-shape" points={HEXAGON} fill={fill} />
      ) : area.area === "phobos_space_haven" ? (
        <polygon className="area-shape" points={ASTEROID} fill={fill} />
      ) : (
        <polygon className="area-shape" points={hexagonPoints(OFF_MARS_RADIUS)} fill={fill} />
      )}
      {area.tile ? <TileMark tile={area.tile} /> : <BonusMarks bonus={area.bonus} />}
      {!area.tile && area.claimed_by !== null && (
        <circle className="claim-marker" r={SIZE * 0.62} stroke={PLAYER_COLOURS[area.claimed_by]} />
      )}
      {area.name && (
        <text className="area-name" y={offMars ? OFF_MARS_RADIUS + 9 : -SIZE * 0.62}>
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

/** A Tile: its colour and drawing show its type, a special Tile's symbol its card, and a cube in its
 * owner's colour whose it is. */
function TileMark({ tile }: { tile: Tile }) {
  const symbol = tile.card ? SPECIAL_SYMBOLS[tile.card] : undefined;
  const markerY = tile.type === "city" ? 9 : tile.type === "special" ? 13 : 0;
  return (
    <g className="tile-mark">
      {tile.type === "ocean" && (
        <path
          className="ocean-waves"
          d="M-15,-6 q3.75,-5 7.5,0 t7.5,0 t7.5,0 t7.5,0 M-15,2 q3.75,-5 7.5,0 t7.5,0 t7.5,0 t7.5,0 M-15,10 q3.75,-5 7.5,0 t7.5,0 t7.5,0 t7.5,0"
        />
      )}
      {tile.type === "greenery" && (
        <path className="greenery-trees" d="M-14,-4 l5,-10 l5,10 z M4,-4 l5,-10 l5,10 z M-14,14 l5,-10 l5,10 z M4,14 l5,-10 l5,10 z" />
      )}
      {tile.type === "city" && <path className="city-skyline" d="M-16,6 v-11 h6 v-7 h7 v10 h6 v-6 h7 v8 h6 v6 z" />}
      {tile.card === "ecological_zone" && <Paw />}
      {symbol && (
        <text className={`special-symbol ${tile.type === "city" ? "on-city" : ""}`} y={tile.type === "city" ? -17 : -4}>
          {symbol}
        </text>
      )}
      {tile.owner !== null && <PlayerCube colour={PLAYER_COLOURS[tile.owner]} y={markerY} size={tile.type === "special" ? 6 : 7.5} />}
    </g>
  );
}

/** Ecological Zone's symbol: drawn, as a browser would take the paw character from a colour emoji font. */
function Paw() {
  return (
    <g className="special-paw" transform="translate(0 -4)">
      <ellipse cy={3.5} rx={6} ry={5} />
      <ellipse cx={-7.5} cy={-2} rx={2.3} ry={3.1} />
      <ellipse cx={-2.8} cy={-6.5} rx={2.3} ry={3.1} />
      <ellipse cx={2.8} cy={-6.5} rx={2.3} ry={3.1} />
      <ellipse cx={7.5} cy={-2} rx={2.3} ry={3.1} />
    </g>
  );
}

/** The placement bonus, one small mark per item, side by side. */
function BonusMarks({ bonus }: { bonus: BonusItem[] }) {
  const spacing = 16;
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
  steel: <BoardIcon path="resources/steel" size={15} />,
  titanium: <BoardIcon path="resources/titanium" size={15} />,
  plant: <BoardIcon path="resources/plant" size={15} />,
  card: <BoardIcon path="resources/card" size={11} height={16} />,
};

/** The tooltip: everything about an Area in words. */
function describe(area: Area, ownerName: string | null, claimantName: string | null, specialName: string | null): string {
  const lines = [area.name ? `${area.area}: ${area.name}` : area.area];
  if (area.reserved === "ocean") lines.push("Reserved for Oceans");
  else if (area.reserved) lines.push(`Reserved for the ${area.name} card`);
  if (area.bonus.length > 0) lines.push(`Placement bonus: ${countBonus(area.bonus)}`);
  if (area.tile) {
    const tile = specialName ? `${specialName} Tile` : TILE_NAMES[area.tile.type];
    lines.push(`${tile}${ownerName ? ` of ${ownerName}` : ""}`);
  }
  if (claimantName) lines.push(`Claimed by ${claimantName} with Land Claim`);
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
