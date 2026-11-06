import { useEffect, useState } from "react";

import { TAGS, type Card, type CardType, type Tag } from "../types";
import { PrintedCard } from "./PrintedCard";

interface Props {
  cards: Card[];
  onClose: () => void;
}

const TYPE_FILTERS: { type: CardType | null; label: string }[] = [
  { type: null, label: "All" },
  { type: "automated", label: "Automated" },
  { type: "active", label: "Active" },
  { type: "event", label: "Event" },
  { type: "corporation", label: "Corporation" },
  { type: "prelude", label: "Prelude Card" },
];

// A card drawn at full size is 248 by 318 pixels; enlarged, it fills the window's height but
// for a margin, up to a limit.
const CARD_HEIGHT = 318;
const ENLARGED_MARGIN = 80;
const LARGEST_SCALE = 2.4;

/** Every card in the card catalog, drawn as on the card list, to browse by type and Tag.
 * Hovering a card enlarges it in place; clicking shows it large until clicked again. */
export function CardGallery({ cards, onClose }: Props) {
  const [type, setType] = useState<CardType | null>(null);
  const [tags, setTags] = useState<Tag[]>([]);
  const [search, setSearch] = useState("");
  const [enlarged, setEnlarged] = useState<Card | null>(null);

  // Escape puts an enlarged card back first, then closes the gallery.
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      if (enlarged) setEnlarged(null);
      else onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [enlarged, onClose]);

  const toggleTag = (tag: Tag) =>
    setTags((previous) => (previous.includes(tag) ? previous.filter((other) => other !== tag) : [...previous, tag]));
  const shown = cards.filter(
    (card) =>
      (type === null || card.type === type) &&
      tags.every((tag) => card.tags.includes(tag)) &&
      matchesSearch(card, search),
  );

  return (
    <div className="card-gallery" role="dialog" aria-labelledby="card-gallery-title">
      <header className="card-gallery-bar">
        <h2 id="card-gallery-title">Cards</h2>
        <div className="segmented" role="group" aria-label="Card type">
          {TYPE_FILTERS.map((filter) => (
            <button
              key={filter.label}
              className={type === filter.type ? "selected" : undefined}
              aria-pressed={type === filter.type}
              onClick={() => setType(filter.type)}
            >
              {filter.label}
            </button>
          ))}
        </div>
        <div className="card-gallery-tags" role="group" aria-label="Tags">
          {TAGS.map((tag) => (
            <button
              key={tag}
              className={`card-gallery-tag${tags.includes(tag) ? " selected" : ""}`}
              aria-pressed={tags.includes(tag)}
              title={`Only cards with ${tag} Tags`}
              onClick={() => toggleTag(tag)}
            >
              <img src={`/card-list/images/tags/${tag}.png`} alt={`${tag} Tag`} />
            </button>
          ))}
        </div>
        <input
          type="text"
          className="card-gallery-search"
          placeholder="Name or number"
          aria-label="Find a card by name or number"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
        <span className="card-gallery-count">
          {shown.length} of {cards.length} cards
        </span>
        <button className="link-button card-gallery-close" onClick={onClose}>
          Close
        </button>
      </header>
      <div className="card-gallery-cards">
        {shown.map((card) => (
          <button
            key={card.id}
            className="card-gallery-card"
            aria-label={`${card.name}: show it large`}
            onClick={() => setEnlarged(card)}
          >
            <PrintedCard card={card} />
          </button>
        ))}
        {shown.length === 0 && <p className="card-gallery-empty">No card matches these filters.</p>}
      </div>
      {enlarged && (
        <div className="card-enlarged" onClick={() => setEnlarged(null)}>
          <div style={{ transform: `scale(${enlargedScale()})` }}>
            <PrintedCard card={enlarged} />
          </div>
        </div>
      )}
    </div>
  );
}

/** Whether `card` has `search` in its name, or is the card with that number: "56" for #056, and
 * "P36" for Prelude's #P36. */
function matchesSearch(card: Card, search: string): boolean {
  const wanted = search.trim().toLowerCase().replace(/^#/, "");
  if (wanted === "") return true;
  const printed = /^(p?)(\d+)$/.exec(wanted);
  if (printed) return card.number === Number(printed[2]) && (card.expansion === "prelude") === (printed[1] === "p");
  return card.name.toLowerCase().includes(wanted);
}

/** How much to enlarge a card so it fits the window's height. */
function enlargedScale(): number {
  return Math.min(LARGEST_SCALE, (window.innerHeight - ENLARGED_MARGIN) / CARD_HEIGHT);
}
