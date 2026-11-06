import type { KeyboardEvent } from "react";

// The board is one picture, as on Board Game Arena: everything on it is placed in these units, and
// the whole of it scales to the window.
export const BOARD_WIDTH = 770;
export const BOARD_HEIGHT = 640;
export const GLOBE_X = 383;
export const GLOBE_Y = 298;
export const GLOBE_RADIUS = 232;

const ICONS = "/card-list/images";

/** The attributes that make a part of the board a button a mouse or a keyboard can press. */
export function svgButton(label: string, press: () => void) {
  return {
    role: "button",
    tabIndex: 0,
    "aria-label": label,
    onClick: press,
    onKeyDown: (event: KeyboardEvent) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        press();
      }
    },
  };
}

/** The points of a hexagon with a corner at the top, centred on (0, 0). */
export function hexagonPoints(radius: number): string {
  return [30, 90, 150, 210, 270, 330]
    .map((degrees) => {
      const angle = (degrees * Math.PI) / 180;
      return `${(radius * Math.cos(angle)).toFixed(2)},${(radius * Math.sin(angle)).toFixed(2)}`;
    })
    .join(" ");
}

/** A Player's marker: a little cube in their colour, its faces shaded. */
export function PlayerCube({ colour, x = 0, y = 0, size = 7 }: { colour: string; x?: number; y?: number; size?: number }) {
  const half = size * 0.866;
  return (
    <g className="player-cube" transform={`translate(${x} ${y})`}>
      <polygon points={`0,${-size} ${half},${-size / 2} ${half},${size / 2} 0,${size} ${-half},${size / 2} ${-half},${-size / 2}`} fill={colour} />
      <polygon points={`0,${-size} ${half},${-size / 2} 0,0 ${-half},${-size / 2}`} fill="rgba(255,255,255,0.4)" />
      <polygon points={`0,0 ${half},${-size / 2} ${half},${size / 2} 0,${size}`} fill="rgba(0,0,0,0.3)" />
    </g>
  );
}

/** One of the card list's icons, centred on (x, y). */
export function BoardIcon({ path, x = 0, y = 0, size, height = size }: { path: string; x?: number; y?: number; size: number; height?: number }) {
  return <image href={`${ICONS}/${path}.png`} x={x - size / 2} y={y - height / 2} width={size} height={height} />;
}
