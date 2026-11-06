import { useEffect, useState } from "react";

import { formatNumber } from "../format";
import type { Card } from "../types";
import { notImplementedNote, printedNumber, useCardsById } from "./catalog";
import { PrintedCard } from "./PrintedCard";

// How much larger than printed the card is drawn, and the size of the whole tooltip, in pixels.
const CARD_ZOOM = 1.2;
const TOOLTIP_WIDTH = 540;
const TOOLTIP_HEIGHT = 400;
const MARGIN = 10;

const TYPE_NAMES: Record<Card["type"], string> = {
  automated: "Automated Project Card",
  active: "Active Project Card",
  event: "Event Project Card",
  corporation: "Corporation",
  prelude: "Prelude Card",
};

/** The card an element asks to enlarge, and where that element is. */
interface Zoomed {
  element: HTMLElement;
  id: string;
  cost: number | undefined;
  note: string | undefined;
}

function zoomedAt(target: EventTarget | null): Zoomed | null {
  const element = target instanceof Element ? target.closest<HTMLElement>("[data-zoom-card]") : null;
  if (!element) return null;
  const { zoomCard, zoomCost, zoomNote } = element.dataset;
  return { element, id: zoomCard!, cost: zoomCost === undefined ? undefined : Number(zoomCost), note: zoomNote };
}

/** Enlarges any card under the mouse or the keyboard's focus, as Board Game Arena's tooltip does: the
 * card large beside the one pointed at, with its details in words. A card asks for this with
 * `data-zoom-card` (its id), and may add `data-zoom-cost` (after discounts) and `data-zoom-note`. */
export function CardZoom({ cards }: { cards: Card[] }) {
  const catalog = useCardsById(cards);
  const [zoomed, setZoomed] = useState<Zoomed | null>(null);
  useEffect(() => {
    const follow = (event: Event) => {
      const next = zoomedAt(event.target);
      setZoomed((current) => (current?.element === next?.element ? current : next));
    };
    // A click usually picks the card, which then goes away from under the mouse.
    const hide = () => setZoomed(null);
    document.addEventListener("mouseover", follow);
    document.addEventListener("focusin", follow);
    document.addEventListener("focusout", hide);
    document.addEventListener("click", hide);
    return () => {
      document.removeEventListener("mouseover", follow);
      document.removeEventListener("focusin", follow);
      document.removeEventListener("focusout", hide);
      document.removeEventListener("click", hide);
    };
  }, []);

  const card = zoomed && catalog.get(zoomed.id);
  if (!zoomed || !card || !zoomed.element.isConnected) return null;
  const costNow = zoomed.cost ?? card.cost;
  const unbuilt = notImplementedNote(card);
  return (
    <aside className="card-zoom" style={placeBeside(zoomed.element.getBoundingClientRect())} aria-hidden>
      <div className="card-zoom-card" style={{ zoom: CARD_ZOOM }}>
        <PrintedCard card={card} cost={zoomed.cost} />
      </div>
      <div className="card-zoom-details">
        <h3>{card.name}</h3>
        <p className="card-zoom-type">
          {TYPE_NAMES[card.type]}
          {card.number !== null && ` · ${printedNumber(card)}`}
        </p>
        {costNow !== null && (
          <p>
            <strong>Cost</strong> {formatNumber(costNow)} MegaCredits
            {costNow !== card.cost && ` (printed ${card.cost})`}
          </p>
        )}
        {card.tags.length > 0 && (
          <p className="card-zoom-tags">
            <strong>Tags</strong>{" "}
            {card.tags.map((tag, position) => (
              <span key={position}>
                <img src={`/card-list/images/tags/${tag}.png`} alt="" /> {tag}
              </span>
            ))}
          </p>
        )}
        {zoomed.note && <p className="card-zoom-note">{zoomed.note}</p>}
        {unbuilt && <p className="card-zoom-note">{unbuilt}</p>}
        <p className="card-zoom-text">{card.text}</p>
      </div>
    </aside>
  );
}

/** Beside the card pointed at, on whichever side there is room, and inside the window. */
function placeBeside(box: DOMRect): { left: number; top: number } {
  const roomOnRight = box.right + MARGIN + TOOLTIP_WIDTH + MARGIN <= window.innerWidth;
  const left = roomOnRight ? box.right + MARGIN : Math.max(MARGIN, box.left - MARGIN - TOOLTIP_WIDTH);
  const lowest = Math.max(MARGIN, window.innerHeight - TOOLTIP_HEIGHT - MARGIN);
  return { left, top: Math.min(Math.max(MARGIN, box.top - 20), lowest) };
}
