import { formatTemperature } from "../players";

const MIN_TEMPERATURE = -30;
const MAX_TEMPERATURE = 8;
const STEP = 2;

// Every step printed on the board's thermometer, hottest first.
const STEPS: number[] = [];
for (let celsius = MAX_TEMPERATURE; celsius >= MIN_TEMPERATURE; celsius -= STEP) STEPS.push(celsius);

/** The thermometer: a column of Temperature steps, filled up to the current one. */
export function TemperatureTrack({ temperature }: { temperature: number }) {
  return (
    <div className="thermometer" aria-label={`Temperature ${formatTemperature(temperature)}`}>
      <div className="thermometer-title">Temperature</div>
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
            {celsius > 0 ? `+${celsius}` : celsius < 0 ? `−${-celsius}` : "0"}
          </li>
        ))}
      </ol>
      <div className="thermometer-bulb" />
      <div className="thermometer-reading">
        {formatTemperature(temperature)}
        {temperature >= MAX_TEMPERATURE && <span className="maxed"> (maximum)</span>}
      </div>
    </div>
  );
}
