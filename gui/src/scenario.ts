// What the state editor does to a Scenario: each edit returns a new one. A card is in one place at
// most, so putting a card somewhere takes it out of wherever it was, deck included.

import type { Card, Scenario, ScenarioPlayer, ScenarioTile } from "./types";

/** Where the state editor puts a card. */
export type CardPile = "hand" | "played_cards";

/** `scenario` with `card` named nowhere, nor anything said about it: it goes into the deck, shuffled
 * beneath the cards the Scenario names there. */
export function takeOutCard(scenario: Scenario, card: string): Scenario {
  const without = (cards: string[]) => cards.filter((each) => each !== card);
  return {
    ...scenario,
    deck: without(scenario.deck),
    discard: without(scenario.discard),
    players: scenario.players.map((player) => ({
      ...player,
      hand: without(player.hand),
      played_cards: without(player.played_cards),
      card_resources: Object.fromEntries(Object.entries(player.card_resources).filter(([id]) => id !== card)),
      used_actions: without(player.used_actions),
      next_card: player.next_card === card ? null : player.next_card,
    })),
  };
}

/** `scenario` with `card` in `pile` of Player `player`, and nowhere else. */
export function putCard(scenario: Scenario, card: string, player: number, pile: CardPile): Scenario {
  const taken = takeOutCard(scenario, card);
  return changePlayer(taken, player, { [pile]: [...taken.players[player][pile], card] });
}

export function changePlayer(scenario: Scenario, player: number, change: Partial<ScenarioPlayer>): Scenario {
  return {
    ...scenario,
    players: scenario.players.map((each, index) => (index === player ? { ...each, ...change } : each)),
  };
}

/** `scenario` with Player `player` holding `corporation`, or none, which no other Player then holds.
 * Whatever was said about the Corporation they held goes with it. */
export function setCorporation(scenario: Scenario, player: number, corporation: string | null): Scenario {
  const players = scenario.players.map((each, index) => {
    if (index === player) {
      const used_actions = each.used_actions.filter((card) => card !== each.corporation);
      return { ...each, corporation, used_actions, first_action_due: false };
    }
    if (corporation === null || each.corporation !== corporation) return each;
    const used_actions = each.used_actions.filter((card) => card !== corporation);
    return { ...each, corporation: null, used_actions, first_action_due: false };
  });
  return { ...scenario, players };
}

/** `scenario` with `tile` on its Area, instead of any Tile there. */
export function placeTile(scenario: Scenario, tile: ScenarioTile): Scenario {
  return { ...scenario, tiles: [...removeTile(scenario, tile.area).tiles, tile] };
}

export function removeTile(scenario: Scenario, area: string): Scenario {
  return { ...scenario, tiles: scenario.tiles.filter((tile) => tile.area !== area) };
}

/** The Tile that `kind` names: "ocean", "greenery", "city", or a special Tile by its card's id. */
export function tileFrom(kind: string, area: string, owner: number): ScenarioTile {
  if (kind === "ocean") return { area, tile: "ocean", owner: null };
  if (kind === "greenery" || kind === "city") return { area, tile: kind, owner };
  // Capital's City is its special Tile too.
  return { area, tile: kind === "capital" ? "city" : "special", card: kind, owner };
}

/** The cards with a special Tile, in catalog order: the "special" of their effect data, and Capital. */
export function cardsWithASpecialTile(cards: Card[]): Card[] {
  return cards.filter((card) => {
    const tiles = (card.effects?.tiles ?? []) as (string | { tile: string })[];
    return card.id === "capital" || tiles.some((tile) => (typeof tile === "string" ? tile : tile.tile) === "special");
  });
}
