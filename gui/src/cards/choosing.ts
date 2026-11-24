import { useState } from "react";

import type { Card, Decision, DecisionOption, Resources } from "../types";
import type { GameUpdate } from "../useGameServer";

/** What buying a dealt card costs, in MegaCredits. */
export const CARD_PRICE = 3;

/** How many of the Prelude Cards dealt at setup each Player keeps. */
export const PRELUDE_CARDS_KEPT = 2;

/** Cards a Player chooses some of: at least `least` and at most `most`, or any number for null. */
export interface ChoiceGroup {
  /** What one is called, and several. */
  noun: string;
  nouns: string;
  cards: string[];
  least: number;
  most: number | null;
  /** What each costs, in MegaCredits. */
  price: number;
}

/** The cards a Decision lets its Player choose, toggled and then sent together with Done (the server's
 * choose_cards). At setup it is everything chosen there. */
export interface Choice {
  /** The Decision it answers. */
  decision: Decision;
  groups: ChoiceGroup[];
  /** What may be spent on them in all, once `chosen` says with which Corporation; null for no limit, and undefined while
   * the Corporation isn't chosen. */
  budget: (chosen: string[]) => number | null | undefined;
}

/** What of a choice is still missing, if anything, what it costs, and what its button says. */
export interface ChoiceState {
  ready: boolean;
  missing: string | null;
  spent: number;
  budget: number | null | undefined;
  button: string;
}

// The Decisions answered with a choice of cards.
const CHOICES = new Set([
  "corporation",
  "prelude_cards",
  "buy_cards",
  "draft",
  "keep_cards",
  "play_prelude_card",
  "sell_patents",
  "discard_to_draw",
]);

function offered(decision: Decision, type: string): string[] {
  return decision.options.filter((option) => option.details.type === type).map((option) => option.details.card as string);
}

function oneOf(cards: string[], noun = "card"): ChoiceGroup {
  return { noun, nouns: `${noun}s`, cards, least: 1, most: 1, price: 0 };
}

/** The choice of cards `decision` asks for, or null if it is answered another way. */
export function choiceFor(game: GameUpdate, catalog: Map<string, Card>): Choice | null {
  const { decision, view } = game;
  if (!decision || !CHOICES.has(decision.kind)) return null;
  const board = view.players[decision.player];
  const free = { decision, budget: () => null };
  switch (decision.kind) {
    case "draft":
      return { ...free, groups: [oneOf(offered(decision, "draft_card"))] };
    case "play_prelude_card":
      return { ...free, groups: [oneOf(offered(decision, "play_prelude_card"))] };
    case "sell_patents": {
      const least = decision.options.some((option) => option.details.type === "done") ? 0 : 1;
      return { ...free, groups: [{ ...oneOf(offered(decision, "sell_card")), least, most: null }] };
    }
    case "discard_to_draw":
      return { ...free, groups: [{ ...oneOf(offered(decision, "discard_card")), least: 0 }] };
    case "keep_cards": {
      const { keep, price } = board.keeping!;
      const cards = offered(decision, price > 0 ? "buy_card" : "keep_card");
      return { ...free, groups: [{ ...oneOf(cards), least: price > 0 ? 0 : keep, most: keep, price }] };
    }
  }
  // At setup, all that is still to be chosen; in a Research phase, only the cards to buy.
  const groups: ChoiceGroup[] = [];
  const corporations = board.choosing_corporation;
  if (corporations && corporations.picked === null) groups.push(oneOf(corporations.dealt, "Corporation"));
  const { dealt, kept } = board.prelude_cards ?? { dealt: [], kept: [] };
  if (view.phase === "setup" && dealt.length > 0 && kept.length < PRELUDE_CARDS_KEPT) {
    const more = PRELUDE_CARDS_KEPT - kept.length;
    const cards = dealt.filter((card) => !kept.includes(card));
    groups.push({ ...oneOf(cards, "Prelude Card"), least: more, most: more });
  }
  const buying = board.buying;
  if (buying) {
    const cards = buying.dealt.filter((card) => !buying.bought.includes(card));
    groups.push({ ...oneOf(cards), least: 0, most: null, price: CARD_PRICE });
  }
  const budget = (chosen: string[]) => {
    const alreadySpent = CARD_PRICE * (buying?.bought.length ?? 0);
    if (!corporations || corporations.picked !== null) return (buying?.megacredits ?? 0) - alreadySpent;
    const corporation = chosen.find((card) => corporations.dealt.includes(card));
    return corporation === undefined ? undefined : startingMegaCredits(catalog.get(corporation));
  };
  return { decision, groups, budget };
}

/** The MegaCredits a Corporation starts with. */
export function startingMegaCredits(corporation: Card | undefined): number {
  return (corporation?.effects?.resources as Partial<Resources> | undefined)?.megacredits ?? 0;
}

/** Where the choice stands with the cards `chosen`. */
export function choiceState(choice: Choice, chosen: string[], catalog: Map<string, Card>): ChoiceState {
  const missing: string[] = [];
  let spent = 0;
  for (const group of choice.groups) {
    const count = group.cards.filter((card) => chosen.includes(card)).length;
    spent += count * group.price;
    const more = group.least - count;
    if (more > 0) missing.push(`${more} ${more === 1 ? group.noun : group.nouns} to choose`);
  }
  const budget = choice.budget(chosen);
  if (budget !== null && budget !== undefined && spent > budget) {
    missing.push(`${spent - budget} MegaCredits too expensive`);
  }
  return {
    ready: missing.length === 0,
    missing: missing.length > 0 ? missing.join(", ") : null,
    spent,
    budget,
    button: buttonText(choice, chosen, catalog),
  };
}

function buttonText(choice: Choice, chosen: string[], catalog: Map<string, Card>): string {
  const card = chosen.length > 0 ? catalog.get(chosen[chosen.length - 1]) : undefined;
  switch (choice.decision.kind) {
    case "play_prelude_card": {
      if (!card) return "Play";
      const option = optionFor(choice.decision, card.id);
      return option?.details.playable === false ? `Discard ${card.name} for 15 MegaCredits` : `Play ${card.name}`;
    }
    case "discard_to_draw":
      return card ? `Discard ${card.name} and draw a card` : "Done, keep the hand";
    default:
      return "Done";
  }
}

/** The Option of `decision` that chooses `card`. */
export function optionFor(decision: Decision, card: string): DecisionOption | undefined {
  return decision.options.find((option) => option.details.card === card);
}

/** The cards chosen so far, and how to toggle one. */
export interface Selection {
  chosen: string[];
  /** Whether `card` is one the Player may toggle now. */
  offers: (card: string) => boolean;
  toggle: (card: string) => void;
}

/** The cards toggled for `choice`, the earliest first. They are kept with the Decision they answer, so a choice taken back
 * with Undo comes back as it was. Choosing one too many lets go of the earliest, so another can be tried with one click. */
export function useSelection(choice: Choice | null, gameNumber: number): Selection {
  const key = choice ? `${gameNumber}/${choice.decision.sequence}` : null;
  const [kept, setKept] = useState<{ key: string | null; chosen: string[] }>({ key: null, chosen: [] });
  const groups = choice?.groups ?? [];
  const groupOf = (card: string) => groups.find((group) => group.cards.includes(card));
  // With one card to play and no other, there is nothing to toggle: the last Prelude Card.
  const only =
    groups.length === 1 && groups[0].least === 1 && groups[0].cards.length === 1 ? [groups[0].cards[0]] : null;
  const chosen = only ?? (kept.key === key ? kept.chosen.filter((card) => groupOf(card) !== undefined) : []);
  const toggle = (card: string) => {
    const group = groupOf(card);
    if (!group) return;
    if (chosen.includes(card)) return setKept({ key, chosen: chosen.filter((other) => other !== card) });
    const inGroup = chosen.filter((other) => group.cards.includes(other));
    const tooMany = group.most !== null && inGroup.length >= group.most;
    setKept({ key, chosen: [...chosen.filter((other) => !(tooMany && other === inGroup[0])), card] });
  };
  return { chosen, offers: (card) => groupOf(card) !== undefined, toggle };
}
