// The messages exchanged with the local server (server/app.py). The view, the
// Decision and the Replay are the engine module's own data, passed through unchanged.

export const CONTROLLERS = ["human", "random_bot"] as const;
export type Controller = (typeof CONTROLLERS)[number];

export interface OptionDetails {
  type: string;
  [key: string]: unknown;
}

export interface DecisionOption {
  index: number;
  label: string;
  details: OptionDetails;
}

export interface Decision {
  player: number;
  kind: string;
  sequence: number;
  options: DecisionOption[];
}

export interface PlayerBoard {
  name: string;
  megacredits: number;
  steel: number;
  titanium: number;
  plants: number;
  production: { megacredits: number };
  terraform_rating: number;
  passed: boolean;
}

export interface Score {
  player: number;
  terraform_rating: number;
  total: number;
}

export type TileType = "ocean" | "greenery" | "city";

export interface Tile {
  type: TileType;
  /** The owning Player, or null for an Ocean. */
  owner: number | null;
}

export type BonusItem = "steel" | "titanium" | "plant" | "card";

/** One Area of the board: what is printed on it, and its Tile if it has one. */
export interface Area {
  /** Its name: "E3" on Mars, or "phobos_space_haven" off Mars. */
  area: string;
  /** The name printed on it, such as "Noctis City". */
  name: string | null;
  /** Row from the top and position from the left on Mars, counted from 1; null off Mars. */
  row: number | null;
  position: number | null;
  /** What the Area is kept for: "ocean", or a card's Tile such as "noctis_city". */
  reserved: string | null;
  bonus: BonusItem[];
  tile: Tile | null;
}

/** One Player's Player View, or the full view. */
export interface View {
  /** The Player whose Player View this is, or null for the full view. */
  viewer: number | null;
  generation: number;
  phase: "action" | "over";
  temperature: number;
  /** In percent. */
  oxygen: number;
  /** How many Ocean Tiles have been placed. */
  oceans: number;
  /** Every Area: on Mars row by row from the top, then off Mars. */
  board: Area[];
  first_player: number;
  current_player: number | null;
  actions_this_turn: number;
  players: PlayerBoard[];
  scores: Score[] | null;
}

/** Where a Game started and the index of every Option picked since. */
export interface Replay {
  start: { settings: { players: number; seed: number } } | { scenario: { seed: number } };
  picks: number[];
}

/** What a saved Replay file holds. */
export interface ReplayFile {
  controllers: Controller[];
  replay: Replay;
}

export interface Update {
  type: "update";
  controllers: Controller[];
  /** The Player whose Player View this is, or null for the full view (Hotseat, or only Random Bots). */
  viewer: number | null;
  seed: number;
  /** Seconds each Random Bot waits before picking. */
  bot_delay: number;
  /** Whether there is an earlier human Decision to go back to. */
  can_undo: boolean;
  view: View;
  /** The current Decision, only when a human must answer it. */
  decision: Decision | null;
  /** Index of the first game log line in `log`; earlier lines were sent before. */
  log_start: number;
  log: string[];
}

export type ServerMessage =
  | Update
  | { type: "game_over"; scores: Score[] }
  | { type: "replay_file"; file: ReplayFile }
  | { type: "error"; message: string };

/** What the setup screen asks for. Without a seed, the server picks one at random. */
export interface NewGameSettings {
  controllers: Controller[];
  seed?: number;
  bot_delay: number;
}

export type ClientMessage =
  | ({ type: "new_game" } & NewGameSettings)
  | { type: "pick"; sequence: number; index: number }
  | { type: "undo" }
  | { type: "save_replay" }
  | { type: "load_replay"; file: unknown; bot_delay: number }
  | { type: "set_bot_delay"; bot_delay: number };
