import type { GameState } from "./useGameServer";

/** Player colours, in seat order, as on Board Game Arena: red, green, blue, yellow, black. */
export const PLAYER_COLOURS = ["#d93a2b", "#3d9b47", "#2f6bd0", "#e2b521", "#3a3a3a"];

/** How a Player is introduced on screen: "You" for the one human, otherwise their name. */
export function playerTitle(game: GameState, player: number): string {
  const humans = game.controllers.filter((controller) => controller === "human").length;
  if (game.controllers[player] === "human" && humans === 1) return "You";
  return game.view.players[player].name;
}

export function controllerLabel(game: GameState, player: number): string {
  return game.controllers[player] === "human" ? "Human" : "Random Bot";
}

/** Temperatures are shown with a real minus sign and an explicit plus. */
export function formatTemperature(celsius: number): string {
  if (celsius > 0) return `+${celsius} °C`;
  if (celsius < 0) return `−${-celsius} °C`;
  return "0 °C";
}
