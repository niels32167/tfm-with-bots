import { createElement, type CSSProperties, type ReactNode } from "react";

import type { Card, FaceElement } from "../types";
import { printedNumber } from "./catalog";
import "./cardList.css";

// The card list's own class for each Project Card type, which picks the frame's colours.
const TYPE_CLASSES = { automated: "automated", active: "active", event: "events" };

/** A card drawn as the fan-made card list draws it (ADR 0005), 248 by 318 pixels: the
 * frame, title, cost, Tags and number come from the card's printed data, and its middle part
 * and the title's style from its face. With a `cost` other than the printed one (a discount),
 * it shows that cost, with the printed one struck through beside it. */
export function PrintedCard({ card, cost }: { card: Card; cost?: number }) {
  const tags = card.tags.map((tag, position) => (
    <div key={position} className={`tag tag${position + 1} tag-${tag}`} title={`${tag} Tag`} />
  ));
  // The elements come in the card list's order, since its layout floats them.
  if (card.type === "corporation") {
    return (
      <div className="printed-card corporation">
        {tags}
        <div className="corporationLabel">CORPORATION</div>
        {setIcon(card, "corporation-icon")}
        {faceElement(card.face.content, "content")}
      </div>
    );
  }
  if (card.type === "prelude") {
    return (
      <div className="printed-card prelude-card">
        <div className="title background-color-prelude" style={styleOf(card.face.title_style)}>
          {card.name}
        </div>
        {tags}
        <div className="prelude-label">PRELUDE</div>
        <div className="number">{printedNumber(card)}</div>
        {setIcon(card, "preludeCard-icon")}
        {faceElement(card.face.content, "content")}
      </div>
    );
  }
  const typeClass = TYPE_CLASSES[card.type];
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
      <div className="number">{printedNumber(card)}</div>
      {setIcon(card, "project-icon")}
      {faceElement(card.face.content, "content")}
    </div>
  );
}

/** The mark of the set a card belongs to, at the place `placeClass` gives it. The base game's cards
 * have none. */
function setIcon(card: Card, placeClass: string): ReactNode {
  if (card.expansion === "prelude") return <div className={`prelude-icon ${placeClass}`} title="Prelude" />;
  return card.corporate_era && <div className={`corporate-icon ${placeClass}`} title="Corporate Era" />;
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
