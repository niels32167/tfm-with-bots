import { formatTemperature, signed } from "../format";
import {
  HEAT_PRODUCTION_BONUS_TEMPERATURES,
  MAX_TEMPERATURE,
  MIN_TEMPERATURE,
  OCEAN_BONUS_TEMPERATURE,
  TEMPERATURE_STEP,
} from "../tracks";
import { BoardIcon, hexagonPoints } from "./boardLayout";

const TUBE_X = 726;
const TUBE_WIDTH = 26;
const TOP_STEP_Y = 92;
const STEP_HEIGHT = 19.2;
const BULB_RADIUS = 29;
// The lowest step is written in the bulb.
const BULB_Y = yOf(MIN_TEMPERATURE) + 4;
const BONUS_X = TUBE_X - TUBE_WIDTH / 2 - 18;

// Every step printed on the tube, hottest first.
const STEPS: number[] = [];
for (let celsius = MAX_TEMPERATURE; celsius > MIN_TEMPERATURE; celsius -= TEMPERATURE_STEP) STEPS.push(celsius);

function yOf(celsius: number): number {
  return TOP_STEP_Y + ((MAX_TEMPERATURE - celsius) / TEMPERATURE_STEP) * STEP_HEIGHT;
}

/** The thermometer: a tube from cold blue to hot red, dark above the current step, which is boxed, a
 * bulb holding the lowest step, and its track bonuses to the left. */
export function TemperatureTrack({ temperature }: { temperature: number }) {
  const top = TOP_STEP_Y - STEP_HEIGHT / 2 - 3;
  const litFrom = yOf(temperature) - STEP_HEIGHT / 2;
  return (
    <g className="thermometer" role="img" aria-label={`Temperature ${formatTemperature(temperature)}`}>
      <rect className="thermometer-tube" x={TUBE_X - TUBE_WIDTH / 2} y={top} width={TUBE_WIDTH} height={BULB_Y - top} rx={TUBE_WIDTH / 2} fill="url(#thermometer-mercury)" />
      {temperature < MAX_TEMPERATURE && (
        <rect className="thermometer-cold" x={TUBE_X - TUBE_WIDTH / 2 + 1} y={top + 1} width={TUBE_WIDTH - 2} height={litFrom - top - 1} rx={TUBE_WIDTH / 2 - 1} />
      )}
      {STEPS.map((celsius) => (
        <g key={celsius} className={`thermometer-step ${celsius === temperature ? "current" : ""}`} transform={`translate(${TUBE_X} ${yOf(celsius)})`}>
          {celsius === temperature && <rect x={-TUBE_WIDTH / 2 - 1} y={-STEP_HEIGHT / 2} width={TUBE_WIDTH + 2} height={STEP_HEIGHT} rx={3} />}
          <text>{signed(celsius)}</text>
        </g>
      ))}
      <g className={`thermometer-bulb ${temperature === MIN_TEMPERATURE ? "current" : ""}`} transform={`translate(${TUBE_X} ${BULB_Y})`}>
        <circle r={BULB_RADIUS} fill="url(#thermometer-bulb)" />
        <text>{formatTemperature(MIN_TEMPERATURE)}</text>
      </g>
      {HEAT_PRODUCTION_BONUS_TEMPERATURES.map((celsius) => (
        <g key={celsius} className="track-bonus" transform={`translate(${BONUS_X} ${yOf(celsius)})`}>
          <title>{`Reaching ${formatTemperature(celsius)} raises heat Production by 1`}</title>
          <rect className="track-bonus-production" x={-11} y={-11} width={22} height={22} rx={3} />
          <BoardIcon path="resources/heat" size={16} />
        </g>
      ))}
      <g className="track-bonus" transform={`translate(${BONUS_X} ${yOf(OCEAN_BONUS_TEMPERATURE)})`}>
        <title>{`Reaching ${formatTemperature(OCEAN_BONUS_TEMPERATURE)} gives an Ocean to place`}</title>
        <polygon className="track-bonus-ocean" points={hexagonPoints(13)} />
        <path className="ocean-waves" d="M-7,-2 q2,-2.5 3.5,0 t3.5,0 t3.5,0 t3.5,0 M-7,3 q2,-2.5 3.5,0 t3.5,0 t3.5,0 t3.5,0" />
      </g>
    </g>
  );
}
