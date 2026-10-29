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

export const RESOURCES = ["megacredits", "steel", "titanium", "plants", "energy", "heat"] as const;
export type Resource = (typeof RESOURCES)[number];

/** An amount of each of the six Resources. */
export type Resources = Record<Resource, number>;

export interface PlayerBoard {
  name: string;
  resources: Resources;
  production: Resources;
  terraform_rating: number;
  passed: boolean;
  hand_size: number;
  /** The cards in hand by catalog id, in card-number order: only the viewer's own, or every
   * hand in the full view; otherwise null. */
  hand: string[] | null;
  /** In the setup or a Research phase, the cards dealt to them to buy from and those of them
   * they have bought so far (nothing is paid until every Player is done): only the viewer's own,
   * or everyone's in the full view; otherwise null. */
  buying: Buying | null;
  /** In the Draft, the cards they keep one from now and pass the rest on, and those kept so far:
   * only the viewer's own, or everyone's in the full view; otherwise null. */
  drafting: Drafting | null;
  /** Every set of cards they passed on in the Draft this Game, in the order passed: only the
   * viewer's own, or everyone's in the full view; otherwise null. */
  passed_in_draft: DraftPass[] | null;
  /** While they play a card such as Business Contacts, the cards they look at to keep some of:
   * only the viewer's own, or everyone's in the full view; otherwise null. */
  keeping: Keeping | null;
  /** The cards played by catalog id, in card-number order, Events included. */
  played_cards: string[];
  /** How many of each Tag are in play. No Tag on a played Event counts, the Event Tag included. */
  tags: Record<CountedTag, number>;
}

/** Cards by catalog id, in card-number order: those dealt, and those of them bought. */
export interface Buying {
  dealt: string[];
  bought: string[];
}

/** Cards by catalog id, in card-number order: those to keep one from, passing the rest to Player
 * `passing_to`, and those kept so far. */
export interface Drafting {
  picking_from: string[];
  kept: string[];
  passing_to: number;
}

/** Cards by catalog id, in card-number order, that `card` lets its Player look at: those they may
 * still keep and those kept so far. They keep `keep` more, and the rest are discarded. */
export interface Keeping {
  card: string;
  looking_at: string[];
  kept: string[];
  keep: number;
}

/** Cards a Player passed on in the Draft, by catalog id in card-number order. */
export interface DraftPass {
  generation: number;
  /** The Player they were passed to. */
  to: number;
  cards: string[];
}

/** One Player's final score. The six Victory Point counts add up to the total. */
export interface Score {
  player: number;
  terraform_rating: number;
  milestones: number;
  awards: number;
  greeneries: number;
  cities: number;
  cards: number;
  total: number;
  /** The tiebreak on equal totals. */
  megacredits: number;
  /** 1 for the winner; Players tied on both total and MegaCredits share a rank. */
  rank: number;
}

/** One Milestone: what it asks for, who claimed it, and how far each Player is towards it. */
export interface Milestone {
  /** Its id, such as "mayor". */
  milestone: string;
  name: string;
  /** As printed: "Owning at least 3 Cities". */
  condition: string;
  /** The count a Player needs to reach. */
  target: number;
  claimed_by: number | null;
  /** Each Player's count towards it, by Player. */
  counts: number[];
}

/** One Award: what it measures, who funded it, and what each Player has of it. */
export interface Award {
  /** Its id, such as "landlord". */
  award: string;
  name: string;
  /** As printed: "Owning the most Tiles in play". */
  condition: string;
  funded_by: number | null;
  /** What each Player has of what it measures, by Player. */
  counts: number[];
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
  /** "setup" is the setup buy before Generation 1, "draft" the Draft that begins a Research phase
   * with the Draft on, and "research" a Research phase, where Players buy cards; "final_greenery"
   * is the final Greenery conversion, after the final Production phase. */
  phase: "setup" | "draft" | "research" | "action" | "final_greenery" | "over";
  temperature: number;
  /** In percent. */
  oxygen: number;
  /** How many Ocean Tiles have been placed. */
  oceans: number;
  /** Every Area: on Mars row by row from the top, then off Mars. */
  board: Area[];
  deck_size: number;
  /** The deck by catalog id from the top down, only in the full view; otherwise null. */
  deck: string[] | null;
  discard_size: number;
  /** The discard pile by catalog id, in card-number order: it lies face down, so only in the
   * full view; otherwise null. */
  discard: string[] | null;
  first_player: number;
  current_player: number | null;
  actions_this_turn: number;
  players: PlayerBoard[];
  /** The five Milestones, in the order printed on the board. */
  milestones: Milestone[];
  /** What claiming a Milestone costs, or null once three are claimed. */
  milestone_cost: number | null;
  /** The five Awards, in the order printed on the board. */
  awards: Award[];
  /** What funding the next Award costs (8, 14 or 20), or null once three are funded. */
  award_cost: number | null;
  scores: Score[] | null;
}

export type CardType = "automated" | "active" | "event" | "corporation";

/** The Tags printed on cards, in the order the gallery offers them as filters. */
export const TAGS = [
  "building",
  "space",
  "power",
  "science",
  "jovian",
  "earth",
  "plant",
  "microbe",
  "animal",
  "city",
  "event",
] as const;
export type Tag = (typeof TAGS)[number];
/** The Tags that count once played: every Tag but the Event Tag. */
export type CountedTag = Exclude<Tag, "event">;

/** An element of a card's face as the card list draws it, with its class names, inline style
 * (CSS property names) and children; text is a string. */
export interface FaceElement {
  tag: "div" | "span" | "br";
  class?: string;
  style?: Record<string, string>;
  children?: (FaceElement | string)[];
}

/** What it takes to draw a card as the card list does, beyond its printed data. */
export interface Face {
  /** The card's middle part. */
  content: FaceElement;
  /** The title's own style, where it has one (a smaller font for long names). */
  title_style?: Record<string, string>;
}

/** A Requirement, such as {"type": "oxygen", "max": 5} or {"type": "tag", "tag": "science", "min": 3}. */
export interface Requirement {
  type: string;
  [key: string]: unknown;
}

/** Fixed Victory Points, or points for something, such as 1 for every 2 microbes on the card. */
export type VictoryPoints =
  | number
  | { points: number; per?: number; at_least?: number; of: Record<string, string> }
  | null;

/** One card of the card catalog, as printed. */
export interface Card {
  /** How Scenarios, Option details and Replays name it: "black_polar_dust". */
  id: string;
  /** 1 to 208 for Project Cards; null for Corporations. */
  number: number | null;
  name: string;
  type: CardType;
  corporate_era: boolean;
  /** In MegaCredits; null for Corporations. */
  cost: number | null;
  /** In the order printed, from the top right corner leftwards. */
  tags: Tag[];
  requirements: Requirement[];
  victory_points: VictoryPoints;
  text: string;
  face: Face;
  /** What an implemented card does when played; cards without it are never offered. */
  effects?: Record<string, unknown>;
}

/** Where a Game started and the index of every Option picked since. */
export interface Replay {
  start:
    | { settings: { players: number; seed: number; implemented_cards_first: boolean; draft: boolean } }
    | { scenario: { seed: number } };
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
  | { type: "card_catalog"; cards: Card[] }
  | Update
  | { type: "game_over"; scores: Score[] }
  | { type: "replay_file"; file: ReplayFile }
  | { type: "error"; message: string };

/** What the setup screen asks for. Without a seed, the server picks one at random. */
export interface NewGameSettings {
  controllers: Controller[];
  seed?: number;
  bot_delay: number;
  /** While most cards are not implemented yet: deal the implemented ones first. */
  implemented_cards_first: boolean;
  /** Whether the Research phases have the Draft. */
  draft: boolean;
}

export type ClientMessage =
  | ({ type: "new_game" } & NewGameSettings)
  | { type: "pick"; sequence: number; index: number }
  | { type: "undo" }
  | { type: "save_replay" }
  | { type: "load_replay"; file: unknown; bot_delay: number }
  | { type: "set_bot_delay"; bot_delay: number };
