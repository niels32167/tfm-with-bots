import { useMemo } from "react";

import type { Card } from "../types";

/** The card catalog by card id, built once for each catalog. */
export function useCardsById(cards: Card[]): Map<string, Card> {
  return useMemo(() => new Map(cards.map((card) => [card.id, card])), [cards]);
}

/** A card's number as printed, "#056" or Prelude's "#P36"; Corporations have none. */
export function printedNumber(card: Card): string | null {
  if (card.number === null) return null;
  return card.expansion === "prelude"
    ? `#P${String(card.number).padStart(2, "0")}`
    : `#${String(card.number).padStart(3, "0")}`;
}

/** Why a card can't be played, if it is not implemented yet; otherwise undefined. */
export function notImplementedNote(card: Card): string | undefined {
  return card.effects === undefined ? "Not implemented yet, so it can't be played" : undefined;
}
