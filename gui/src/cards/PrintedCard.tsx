import { createElement, type CSSProperties, type ReactNode } from "react";

import type { Card, CardType, FaceElement } from "../types";
import "./cardList.css";

// The card list's own class for each card type, which picks the frame's colours.
const TYPE_CLASSES: Record<CardType, string> = {
  automated: "automated",
  active: "active",
  event: "events",
  corporation: "corporation",
};

/** A card drawn as the fan-made card list draws it (ADR 0005), 248 by 318 pixels: the
 * frame, title, cost, Tags and number come from the card's printed data, and its middle part
 * and the title's style from its face. With a `cost` other than the printed one (a discount),
 * it shows that cost, with the printed one struck through beside it. */
export function PrintedCard({ card, cost }: { card: Card; cost?: number }) {
  const typeClass = TYPE_CLASSES[card.type];
  const tags = card.tags.map((tag, position) => (
    <div key={position} className={`tag tag${position + 1} tag-${tag}`} title={`${tag} Tag`} />
  ));
  // The elements come in the card list's order, since its layout floats them.
  if (card.type === "corporation") {
    return (
      <div className="printed-card corporation">
        {tags}
        <div className="corporationLabel">CORPORATION</div>
        {card.corporate_era && <div className="corporate-icon corporation-icon" title="Corporate Era" />}
        {faceElement(card.face.content, "content")}
      </div>
    );
  }
  return (
    <div className={`printed-card ${typeClass}`}>
      <div className={`title background-color-${typeClass}`} style={styleOf(card.face.title_style)}>
        {card.name}
      </div>
      {cost === undefined || cost === card.cost ? (
        <div className="price">{card.cost}</div>
      ) : (
        <div className="price discounted" title={`Printed cost ${card.cost} MegaCredits, ${cost} after discounts`}>
          {cost}
          <s className="printed-price">{card.cost}</s>
        </div>
      )}
      {tags}
      <div className="number">#{String(card.number).padStart(3, "0")}</div>
      {card.corporate_era && <div className="corporate-icon project-icon" title="Corporate Era" />}
      {faceElement(card.face.content, "content")}
    </div>
  );
}

/** Part of a card's face as a React node, with its children. */
function faceElement(part: FaceElement | string, key: number | string): ReactNode {
  if (typeof part === "string") return part;
  if (part.tag === "br") return <br key={key} />;
  const children = part.children?.map((child, position) => faceElement(child, position));
  return createElement(part.tag, { key, className: part.class, style: styleOf(part.style) }, children);
}

/** An inline style from the card list as a React style: "margin-left" becomes marginLeft.
 * Vendor-prefixed declarations (-webkit-transform…) are left out; each comes with the
 * standard one, which modern browsers use. */
function styleOf(style: Record<string, string> | undefined): CSSProperties | undefined {
  if (!style) return undefined;
  const entries = Object.entries(style)
    .filter(([property]) => !property.startsWith("-"))
    .map(([property, value]) => [property.replace(/-([a-z])/g, (_, letter: string) => letter.toUpperCase()), value]);
  return Object.fromEntries(entries) as CSSProperties;
}
