import type { TileType } from "./types";

export const TILE_NAMES: Record<TileType, string> = { ocean: "Ocean", greenery: "Greenery", city: "City" };

/** A number with a real minus sign when it is negative: "8", "0", "−5". */
export function formatNumber(value: number): string {
  return value < 0 ? `−${-value}` : `${value}`;
}

/** A number with an explicit sign and a real minus sign: "+8", "0", "−30". */
export function signed(value: number): string {
  return value > 0 ? `+${value}` : formatNumber(value);
}

export function formatTemperature(celsius: number): string {
  return `${signed(celsius)} °C`;
}
