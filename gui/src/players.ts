import type { ControllerName, ControllerOnOffer } from "./types";
import type { GameUpdate } from "./useGameServer";

/** Player colours, in Player order, as on Board Game Arena: red, green, blue, yellow, black. */
export const PLAYER_COLOURS = ["#d93a2b", "#3d9b47", "#2f6bd0", "#e2b521", "#3a3a3a"];


/** Whether `player` is the one human at the screen, whose Player View is shown and who is addressed as "You". */
export function isYou(game: GameUpdate, player: number): boolean {
  return game.viewer === player;
}

/** How a Player is introduced on screen: "You" for the one human, otherwise their name. */
export function playerTitle(game: GameUpdate, player: number): string {
  return isYou(game, player) ? "You" : game.view.players[player].name;
}

/** How the setup screen names `controller`, among those `offered`; its own name if it isn't offered. */
export function controllerLabel(offered: ControllerOnOffer[], controller: ControllerName): string {
  return offered.find((candidate) => candidate.name === controller)?.label ?? controller;
}
