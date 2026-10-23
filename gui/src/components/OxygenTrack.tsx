import { MAX_OXYGEN, TEMPERATURE_BONUS_OXYGEN } from "../tracks";

// The arc runs over the top of Mars, from 0 % on the left to 14 % on the right. Angles are
// in degrees, clockwise from the right, as SVG draws them; -90 is straight up.
const FIRST_ANGLE = -160;
const LAST_ANGLE = -20;
const CELL_RADIUS = 14;

const LEVELS = Array.from({ length: MAX_OXYGEN + 1 }, (_, level) => level);

/** The Oxygen track as an arc of steps around Mars, `radius` from its centre, filled up to the current level. */
export function OxygenTrack({ oxygen, radius }: { oxygen: number; radius: number }) {
  const [startX, startY] = pointAt(0, radius);
  const [endX, endY] = pointAt(MAX_OXYGEN, radius);
  return (
    <g className="oxygen-track" role="img" aria-label={`Oxygen ${oxygen} %`}>
      <path
        className="oxygen-band"
        d={`M ${startX} ${startY} A ${radius} ${radius} 0 0 1 ${endX} ${endY}`}
        strokeWidth={2 * CELL_RADIUS + 6}
      />
      {LEVELS.map((level) => {
        const [x, y] = pointAt(level, radius);
        const classes = ["oxygen-step", level <= oxygen ? "filled" : "", level === oxygen ? "current" : ""];
        return (
          <g key={level} className={classes.join(" ")} transform={`translate(${x} ${y})`}>
            <circle r={CELL_RADIUS} />
            <text>{level}</text>
          </g>
        );
      })}
      <TemperatureBonusMark radius={radius} />
      <OxygenReading oxygen={oxygen} radius={radius} />
    </g>
  );
}

/** The track's title and current level, in the corner outside the start of the arc. */
function OxygenReading({ oxygen, radius }: { oxygen: number; radius: number }) {
  const corner = (radius + 5 * CELL_RADIUS) * Math.SQRT1_2;
  return (
    <g transform={`translate(${-corner} ${-corner})`}>
      <text className="oxygen-title">OXYGEN</text>
      <text className="oxygen-reading" y={18}>
        {oxygen} %
      </text>
      {oxygen >= MAX_OXYGEN && (
        <text className="maxed" y={34}>
          (maximum)
        </text>
      )}
    </g>
  );
}

/** A small thermometer just inside the 8 % step: reaching it also raises Temperature. */
function TemperatureBonusMark({ radius }: { radius: number }) {
  const [x, y] = pointAt(TEMPERATURE_BONUS_OXYGEN, radius - 2 * CELL_RADIUS);
  return (
    <g className="track-bonus temperature-bonus" transform={`translate(${x} ${y})`}>
      <title>{`Reaching ${TEMPERATURE_BONUS_OXYGEN} % Oxygen also raises Temperature one step`}</title>
      <rect x={-2.5} y={-9} width={5} height={13} rx={2.5} />
      <circle cy={5} r={4.5} />
    </g>
  );
}

/** Where `level` sits on an arc of `radius`, as [x, y]. */
function pointAt(level: number, radius: number): [number, number] {
  const degrees = FIRST_ANGLE + ((LAST_ANGLE - FIRST_ANGLE) * level) / MAX_OXYGEN;
  const angle = (degrees * Math.PI) / 180;
  return [Number((radius * Math.cos(angle)).toFixed(2)), Number((radius * Math.sin(angle)).toFixed(2))];
}
