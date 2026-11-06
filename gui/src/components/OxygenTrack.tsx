import { MAX_OXYGEN, TEMPERATURE_BONUS_OXYGEN } from "../tracks";
import { BoardIcon, GLOBE_RADIUS, GLOBE_X, GLOBE_Y } from "./boardLayout";

// The arc runs over the top of Mars, from 0 % on the left to 14 % on the right. Angles are
// in degrees, clockwise from the right, as SVG draws them; -90 is straight up.
const FIRST_ANGLE = -143;
const LAST_ANGLE = -37;
const RADIUS = GLOBE_RADIUS + 22;
const BAND_WIDTH = 30;

const LEVELS = Array.from({ length: MAX_OXYGEN + 1 }, (_, level) => level);
// The track's icon sits just past each end of the arc.
const ICONS_AT = [-0.95, MAX_OXYGEN + 0.95];

/** The Oxygen track: a silver band over Mars, lit up to the current level, which is ringed. */
export function OxygenTrack({ oxygen }: { oxygen: number }) {
  return (
    <g className="oxygen-track" role="img" aria-label={`Oxygen ${oxygen} %`}>
      <path className="oxygen-band" d={arc(0, MAX_OXYGEN)} strokeWidth={BAND_WIDTH} stroke="url(#oxygen-band)" />
      {oxygen > 0 && <path className="oxygen-lit" d={arc(0, oxygen)} strokeWidth={BAND_WIDTH - 8} />}
      {LEVELS.map((level) => {
        const [x, y] = pointAt(level);
        const classes = ["oxygen-step", level === oxygen ? "current" : "", level === MAX_OXYGEN ? "last" : ""];
        return (
          <g key={level} className={classes.join(" ")} transform={`translate(${x} ${y})`}>
            {level === oxygen && <circle r={14} />}
            <text>{level}</text>
          </g>
        );
      })}
      {ICONS_AT.map((level) => {
        const [x, y] = pointAt(level);
        return <BoardIcon key={level} path="global-parameters/oxygen" x={x} y={y} size={22} />;
      })}
      <TemperatureBonusMark />
    </g>
  );
}

/** A small thermometer just outside the 8 % step: reaching it also raises Temperature. */
function TemperatureBonusMark() {
  const [x, y] = pointAt(TEMPERATURE_BONUS_OXYGEN, RADIUS + 27);
  return (
    <g className="temperature-bonus" transform={`translate(${x} ${y})`}>
      <title>{`Reaching ${TEMPERATURE_BONUS_OXYGEN} % Oxygen also raises Temperature one step`}</title>
      <BoardIcon path="global-parameters/temperature" size={7} height={22} />
    </g>
  );
}

/** The path of the arc from one level to another. */
function arc(from: number, to: number): string {
  const [startX, startY] = pointAt(from);
  const [endX, endY] = pointAt(to);
  return `M ${startX} ${startY} A ${RADIUS} ${RADIUS} 0 0 1 ${endX} ${endY}`;
}

/** Where `level` sits on an arc of `radius` round Mars, as [x, y]. */
function pointAt(level: number, radius: number = RADIUS): [number, number] {
  const degrees = FIRST_ANGLE + ((LAST_ANGLE - FIRST_ANGLE) * level) / MAX_OXYGEN;
  const angle = (degrees * Math.PI) / 180;
  return [
    Number((GLOBE_X + radius * Math.cos(angle)).toFixed(2)),
    Number((GLOBE_Y + radius * Math.sin(angle)).toFixed(2)),
  ];
}
