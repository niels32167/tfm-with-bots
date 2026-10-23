import { formatTemperature, signed } from "../format";
import {
  HEAT_PRODUCTION_BONUS_TEMPERATURES,
  MAX_TEMPERATURE,
  MIN_TEMPERATURE,
  OCEAN_BONUS_TEMPERATURE,
  TEMPERATURE_STEP,
} from "../tracks";

// Every step printed on the board's thermometer, hottest first.
const STEPS: number[] = [];
for (let celsius = MAX_TEMPERATURE; celsius >= MIN_TEMPERATURE; celsius -= TEMPERATURE_STEP) STEPS.push(celsius);

/** The thermometer: a column of Temperature steps, filled up to the current one, with its track bonuses. */
export function TemperatureTrack({ temperature }: { temperature: number }) {
  return (
    <div className="thermometer" aria-label={`Temperature ${formatTemperature(temperature)}`}>
      <div className="track-title">Temperature</div>
      <ol className="thermometer-steps">
        {STEPS.map((celsius) => (
          <li
            key={celsius}
            className={[
              "thermometer-step",
              celsius <= temperature ? "filled" : "",
              celsius === temperature ? "current" : "",
            ].join(" ")}
          >
            {signed(celsius)}
            <TrackBonus celsius={celsius} />
          </li>
        ))}
      </ol>
      <div className="thermometer-bulb" />
      <div className="track-reading">
        {formatTemperature(temperature)}
        {temperature >= MAX_TEMPERATURE && <span className="maxed"> (maximum)</span>}
      </div>
    </div>
  );
}

/** The bonus printed beside a step, if any: heat Production, or an Ocean. */
function TrackBonus({ celsius }: { celsius: number }) {
  const reaching = `Reaching ${formatTemperature(celsius)}`;
  if (HEAT_PRODUCTION_BONUS_TEMPERATURES.includes(celsius)) {
    return (
      <span className="track-bonus heat-production" title={`${reaching} raises heat Production by 1`}>
        +1
      </span>
    );
  }
  if (celsius === OCEAN_BONUS_TEMPERATURE) {
    return <span className="track-bonus ocean-bonus" title={`${reaching} gives an Ocean to place`} />;
  }
  return null;
}
