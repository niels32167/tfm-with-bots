import { useCallback, useEffect, useState } from "react";

import { HAND_OPTIONS } from "./cards/HandDock";
import type { Advice, Decision } from "./types";
import type { GameUpdate } from "./useGameServer";

const ADVICE_KEY = "terraforming-mars-advice";

/** Whether the bot's advice is asked for, and of which bot, or null for the one suggested: kept in this browser. */
export function useAdviceSwitch() {
  const [kept, setKept] = useState<{ on: boolean; bot: string | null }>(() => {
    try {
      return { on: false, bot: null, ...JSON.parse(window.localStorage.getItem(ADVICE_KEY) ?? "{}") };
    } catch {
      return { on: false, bot: null };
    }
  });
  const change = useCallback((next: { on: boolean; bot: string | null }) => {
    setKept(next);
    try {
      window.localStorage.setItem(ADVICE_KEY, JSON.stringify(next));
    } catch {
      // Storage may be blocked; the switch then lasts as long as the page.
    }
  }, []);
  return [kept, change] as const;
}

/** The advice for the Decision `game` waits on: asked of the bot chosen while the switch is on, again for each Decision.
 * Null while it isn't there. */
export function useAdvice(
  game: GameUpdate | null,
  gameNumber: number,
  on: boolean,
  bot: string | null,
  latest: Advice | null,
  ask: (sequence: number, controller: string) => void,
): { bot: string | null; advice: Advice | null } {
  const advisers = game?.advisers ?? [];
  const asked = bot !== null && advisers.includes(bot) ? bot : (advisers[0] ?? null);
  const sequence = game?.decision?.sequence;
  useEffect(() => {
    if (on && asked !== null && sequence !== undefined) ask(sequence, asked);
  }, [on, asked, sequence, gameNumber, ask]);
  const current = latest !== null && latest.sequence === sequence && latest.controller === asked;
  return { bot: asked, advice: on && current ? latest : null };
}

/** The index of the Option the advice would pick now, or null. */
export function advisedOption(advice: Advice | null): number | null {
  return advice?.decisions[0]?.picked ?? null;
}

/** The cards the advice for `decision` would choose, or the one it would play from the hand. */
export function cardsAdvised(advice: Advice, decision: Decision): string[] {
  if (advice.cards.length > 0) return advice.cards;
  const index = advisedOption(advice);
  const details = decision.options.find((option) => option.index === index)?.details;
  return details && details.type in HAND_OPTIONS ? [details.card as string] : [];
}
