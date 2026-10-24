import { type RefObject, useLayoutEffect, useState } from "react";

// A printed card's size at zoom 1, as the card list draws it (cardList.css): 240 by 310 pixels
// inside, plus its frame.
const CARD_WIDTH = 247;
const CARD_HEIGHT = 317;

const MIN_ZOOM = 0.35;
const MAX_ZOOM = 1;
// Space kept free below the cards, above the hand dock or the window's bottom edge.
const BOTTOM_MARGIN = 16;

/** The largest zoom (at most 1) at which `count` cards, laid out in a grid with `gap` pixels
 * between them, fit the element `ref` points to: its width, and the height from its top down to
 * the hand dock (the --hand-dock-height the page leaves for it at the bottom of the window), so
 * that every card is in view without scrolling. */
export function useFitZoom(ref: RefObject<HTMLElement | null>, count: number, gap: number): number {
  const [zoom, setZoom] = useState(MAX_ZOOM);
  useLayoutEffect(() => {
    const element = ref.current;
    if (!element) return;
    const fit = () => {
      const box = element.getBoundingClientRect();
      const dock = parseFloat(getComputedStyle(element).getPropertyValue("--hand-dock-height")) || 0;
      const height = window.innerHeight - dock - Math.max(box.top, 0) - BOTTOM_MARGIN;
      setZoom(bestZoom(count, box.width, height, gap));
    };
    fit();
    const observer = new ResizeObserver(fit);
    observer.observe(element);
    window.addEventListener("resize", fit);
    return () => {
      observer.disconnect();
      window.removeEventListener("resize", fit);
    };
  }, [ref, count, gap]);
  return zoom;
}

/** Tries every number of columns and keeps the one that lets the cards be largest. */
function bestZoom(count: number, width: number, height: number, gap: number): number {
  let best = MIN_ZOOM;
  for (let columns = 1; columns <= Math.max(count, 1); columns++) {
    const rows = Math.ceil(count / columns);
    const across = (width - gap * (columns - 1)) / (columns * CARD_WIDTH);
    const down = (height - gap * (rows - 1)) / (rows * CARD_HEIGHT);
    best = Math.max(best, Math.min(across, down));
  }
  // Rounded down, so that rounding in the browser never pushes the last card of a row onto the next.
  return Math.min(Math.floor(best * 100) / 100, MAX_ZOOM);
}
