import { MAX_OCEANS } from "../tracks";
import { hexagonPoints } from "./boardLayout";

/** The Ocean counter: as on Board Game Arena, a blue hexagon holding how many Oceans are left to place. */
export function OceanTrack({ oceans }: { oceans: number }) {
  return (
    <g className="ocean-counter" transform="translate(655 58)" role="img" aria-label={`Oceans ${oceans} of ${MAX_OCEANS}`}>
      <title>{`${oceans} of ${MAX_OCEANS} Oceans placed`}</title>
      <polygon className="ocean-counter-rim" points={hexagonPoints(38)} />
      <polygon points={hexagonPoints(32)} fill="url(#tile-ocean)" />
      <text>{MAX_OCEANS - oceans}</text>
      <text className="ocean-counter-label" y={50}>
        Oceans left
      </text>
    </g>
  );
}
