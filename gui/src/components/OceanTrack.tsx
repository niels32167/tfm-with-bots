import { MAX_OCEANS } from "../tracks";

// One slot per Ocean, the last first, so the column fills from the bottom like the thermometer.
const SLOTS = Array.from({ length: MAX_OCEANS }, (_, index) => MAX_OCEANS - index);

/** The Ocean counter: a column of 9 slots, one filled for each Ocean placed. */
export function OceanTrack({ oceans }: { oceans: number }) {
  return (
    <div className="ocean-track" aria-label={`Oceans ${oceans} of ${MAX_OCEANS}`}>
      <div className="track-title">Oceans</div>
      <ol className="ocean-slots">
        {SLOTS.map((count) => (
          <li key={count} className={`ocean-slot ${count <= oceans ? "placed" : ""}`}>
            {count}
          </li>
        ))}
      </ol>
      <div className="track-reading">
        {oceans} of {MAX_OCEANS}
        {oceans >= MAX_OCEANS && <span className="maxed"> (maximum)</span>}
      </div>
    </div>
  );
}
