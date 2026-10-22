// The messages exchanged with the local server (server/app.py). The view and the
// Decision are the engine module's own data, passed through unchanged.

export type Controller = "human" | "random_bot";

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
  production: { megacredits: number };
  terraform_rating: number;
  passed: boolean;
}

export interface Score {
  player: number;
  terraform_rating: number;
  total: number;
}

export interface PlayerView {
  viewer: number;
  generation: number;
  phase: "action" | "over";
  temperature: number;
  current_player: number | null;
  actions_this_turn: number;
  players: PlayerBoard[];
  scores: Score[] | null;
}

export interface Update {
  type: "update";
  controllers: Controller[];
  viewer: number;
  view: PlayerView;
  /** The current Decision, only when a human must answer it. */
  decision: Decision | null;
  /** Index of the first game log line in `log`; earlier lines were sent before. */
  log_start: number;
  log: string[];
}

export type ServerMessage =
  | Update
  | { type: "game_over"; scores: Score[] }
  | { type: "error"; message: string };

export type ClientMessage =
  | { type: "new_game"; controllers: Controller[]; seed?: number; bot_delay?: number }
  | { type: "pick"; sequence: number; index: number };
