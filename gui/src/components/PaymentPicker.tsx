import { useState } from "react";

import type { Decision } from "../types";

interface Props {
  /** A payment Decision: one Option for each way to pay. */
  decision: Decision;
  disabled: boolean;
  onPay: (index: number) => void;
}

/** What may be put towards a cost besides MegaCredits: microbes from Psychrophiles too. */
type Part = "steel" | "titanium" | "heat" | "microbes";
const PARTS: readonly Part[] = ["steel", "titanium", "heat", "microbes"];
/** Each part's icon, among the card list's Resource images. */
const ICON_FILES: Record<Part, string> = { steel: "steel", titanium: "titanium", heat: "heat", microbes: "microbe" };
const ICONS = "/card-list/images";

/** The id of the card a payment Decision is about, or null for any other Decision and for a payment
 * that is about something else, such as a Standard Project. */
export function cardBeingPaidFor(decision: Decision | null): string | null {
  return decision?.kind === "payment" ? ((decision.options[0].details.card as string | undefined) ?? null) : null;
}

/** One way to pay, from an Option's details. */
interface Split {
  index: number;
  megacredits: number;
  steel: number;
  titanium: number;
  heat: number;
  microbes: number;
}

/** Steppers for the steel, titanium, heat and microbes to put towards a cost, with the MegaCredits that leaves
 * to pay, instead of one button per way to pay. The steppers reach only the offered ways,
 * starting from the first (the most MegaCredits). Remount it for each Decision. */
export function PaymentPicker({ decision, disabled, onPay }: Props) {
  const splits: Split[] = decision.options.map((option) => ({
    index: option.index,
    megacredits: option.details.megacredits as number,
    steel: option.details.steel as number,
    titanium: option.details.titanium as number,
    heat: option.details.heat as number,
    // Left out of the details unless microbes pay part of it.
    microbes: (option.details.microbes as number | undefined) ?? 0,
  }));
  const [chosen, setChosen] = useState(0);
  const split = splits[chosen];
  const parts = PARTS.filter((part) => splits.some((each) => each[part] > 0));

  /** The offered way with one step more (or less) of `part` than the chosen one, as close to
   * it as can be in the others; null if there is none. */
  const step = (part: Part, direction: 1 | -1): number | null => {
    const others = PARTS.filter((other) => other !== part);
    const distance = (each: Split) => [
      direction * (each[part] - split[part]),
      others.reduce((total, other) => total + Math.abs(each[other] - split[other]), 0),
    ];
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
      {parts.map((part) => {
        const less = step(part, -1);
        const more = step(part, 1);
        return (
          <span key={part} className="payment-stepper">
            <button
              className="stepper-button"
              aria-label={`Less ${part}`}
              disabled={disabled || less === null}
              onClick={() => less !== null && setChosen(less)}
            >
              −
            </button>
            <span className="payment-amount" title={`${split[part]} ${part}`}>
              <img src={`${ICONS}/resources/${ICON_FILES[part]}.png`} alt={part} />
              {split[part]}
            </span>
            <button
              className="stepper-button"
              aria-label={`More ${part}`}
              disabled={disabled || more === null}
              onClick={() => more !== null && setChosen(more)}
            >
              +
            </button>
          </span>
        );
      })}
      <span className="payment-amount" title={`${split.megacredits} MegaCredit${split.megacredits === 1 ? "" : "s"}`}>
        <img src={`${ICONS}/megacredits/megacredit.png`} alt="MegaCredits" />
        {split.megacredits}
      </span>
      <button className="option" disabled={disabled} onClick={() => onPay(split.index)}>
        Pay
      </button>
    </span>
  );
}
