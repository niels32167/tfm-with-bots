import { formatTemperature } from "../format";
import { MAX_OCEANS, MAX_OXYGEN, MAX_TEMPERATURE } from "../tracks";
import type { View } from "../types";

/** The box above the player boards, as on Board Game Arena: the Global Parameters and the Generation,
 * in view even when the board has scrolled away. Oceans are those placed, as there, where the board's
 * counter holds those left. A Global Parameter at its maximum says so. */
export function GlobalReadings({ view }: { view: View }) {
  return (
    <dl className="global-readings" aria-label="Global Parameters and Generation">
      <Reading name="Oxygen" icon="global-parameters/oxygen" value={`${view.oxygen} %`} maxed={view.oxygen >= MAX_OXYGEN} />
      <Reading
        name="Temperature"
        icon="global-parameters/temperature"
        value={formatTemperature(view.temperature)}
        maxed={view.temperature >= MAX_TEMPERATURE}
      />
      <Reading name={`Oceans placed, of ${MAX_OCEANS}`} icon="tiles/ocean" value={`${view.oceans}`} maxed={view.oceans >= MAX_OCEANS} />
      <Reading name="Generation" icon="mars" value={`${view.generation}`} />
    </dl>
  );
}

function Reading({ name, icon, value, maxed = false }: { name: string; icon: string; value: string; maxed?: boolean }) {
  return (
    <div className={`global-reading ${maxed ? "maxed" : ""}`} title={maxed ? `${name} (maximum)` : name}>
      <dt>
        <img src={`/card-list/images/${icon}.png`} alt={name} />
      </dt>
      <dd>
        {value}
        {maxed && <span className="global-reading-maximum"> max</span>}
      </dd>
    </div>
  );
}
