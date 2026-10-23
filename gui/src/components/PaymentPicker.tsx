import { useState } from "react";

import type { Decision } from "../types";

interface Props {
  /** A payment Decision: one Option for each way to pay. */
  decision: Decision;
  disabled: boolean;
  onPay: (index: number) => void;
}

type Cube = "steel" | "titanium";

/** The id of the card a payment Decision is about, or null for any other Decision. */
export function cardBeingPaidFor(decision: Decision | null): string | null {
  return decision?.kind === "payment" ? (decision.options[0].details.card as string) : null;
}

/** One way to pay, from an Option's details. */
interface Split {
  index: number;
  megacredits: number;
  steel: number;
  titanium: number;
}

/** Steppers for the steel and titanium to put towards a card, with the MegaCredits that leaves
 * to pay, instead of one button per way to pay. The steppers reach only the offered ways,
 * starting from the first (the most MegaCredits). Remount it for each Decision. */
export function PaymentPicker({ decision, disabled, onPay }: Props) {
  const splits: Split[] = decision.options.map((option) => ({
    index: option.index,
    megacredits: option.details.megacredits as number,
    steel: option.details.steel as number,
    titanium: option.details.titanium as number,
  }));
  const [chosen, setChosen] = useState(0);
  const split = splits[chosen];
  const cubes = (["steel", "titanium"] as const).filter((cube) => splits.some((each) => each[cube] > 0));

  /** The offered way with one step more (or less) of `cube` than the chosen one, as close to
   * it as can be in the other cube; null if there is none. */
  const step = (cube: Cube, direction: 1 | -1): number | null => {
    const other: Cube = cube === "steel" ? "titanium" : "steel";
    const distance = (each: Split) => [direction * (each[cube] - split[cube]), Math.abs(each[other] - split[other])];
    let best: number | null = null;
    for (const [position, each] of splits.entries()) {
      const [along, across] = distance(each);
      if (along <= 0) continue;
      const [bestAlong, bestAcross] = best === null ? [Infinity, Infinity] : distance(splits[best]);
      if (along < bestAlong || (along === bestAlong && across < bestAcross)) best = position;
    }
    return best;
  };

  return (
    <span className="payment-picker">
      {cubes.map((cube) => {
        const less = step(cube, -1);
        const more = step(cube, 1);
        return (
          <span key={cube} className="payment-stepper">
            <button
              className="stepper-button"
              aria-label={`Less ${cube}`}
              disabled={disabled || less === null}
              onClick={() => less !== null && setChosen(less)}
            >
              −
            </button>
            <span className="payment-amount">
              {split[cube]} {cube}
            </span>
            <button
              className="stepper-button"
              aria-label={`More ${cube}`}
              disabled={disabled || more === null}
              onClick={() => more !== null && setChosen(more)}
            >
              +
            </button>
          </span>
        );
      })}
      <span className="payment-amount">
        and {split.megacredits} MegaCredit{split.megacredits === 1 ? "" : "s"}
      </span>
      <button className="option" disabled={disabled} onClick={() => onPay(split.index)}>
        Pay
      </button>
    </span>
  );
}
