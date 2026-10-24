import { useMemo } from "react";

import type { Card } from "../types";

/** The card catalog by card id, built once for each catalog. */
export function useCardsById(cards: Card[]): Map<string, Card> {
  return useMemo(() => new Map(cards.map((card) => [card.id, card])), [cards]);
}

/** Why a card can't be played, if it is not implemented yet; otherwise undefined. */
export function notImplementedNote(card: Card): string | undefined {
  return card.effects === undefined ? "Not implemented yet, so it can't be played" : undefined;
}
