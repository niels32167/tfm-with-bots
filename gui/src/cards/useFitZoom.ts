import { type RefObject, useLayoutEffect, useRef, useState } from "react";

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
  return useZoom(
    ref,
    (box, dock) => bestZoom(count, box.width, window.innerHeight - dock - Math.max(box.top, 0) - BOTTOM_MARGIN, gap),
    `${count}/${gap}`,
  );
}

/** The zoom `fit` finds for the element's box and the hand dock's height, again whenever either or `key` changes. */
function useZoom(
  ref: RefObject<HTMLElement | null>,
  fit: (box: DOMRect, dock: number) => number,
  key: string,
): number {
  const [zoom, setZoom] = useState(MAX_ZOOM);
  const latestFit = useRef(fit);
  latestFit.current = fit;
  useLayoutEffect(() => {
    const element = ref.current;
    if (!element) return;
    const update = () => {
      const dock = parseFloat(getComputedStyle(element).getPropertyValue("--hand-dock-height")) || 0;
      setZoom(latestFit.current(element.getBoundingClientRect(), dock));
    };
    update();
    const observer = new ResizeObserver(update);
    observer.observe(element);
    window.addEventListener("resize", update);
    return () => {
      observer.disconnect();
      window.removeEventListener("resize", update);
    };
  }, [ref, key]);
  return zoom;
}

// What a row's title and the space around it take, in pixels.
const ROW_TITLE_HEIGHT = 42;
const MIN_ROW_ZOOM = 0.3;

/** At setup, the zoom of row `row` of several, of `counts` cards each, so that all of them are in view at once in the
 * space from the top of the rows around the element `ref` points to down to the hand dock: each row on one line, the one with the most
 * cards as large as its line allows and no taller than its share, and the others sharing the height left. */
export function useRowZoom(
  ref: RefObject<HTMLElement | null>,
  counts: number[],
  row: number,
  gap: number,
): number {
  const fit = (box: DOMRect, dock: number) => {
    const top = ref.current?.closest(".buying-panel-rows")?.getBoundingClientRect().top ?? box.top;
    const height = window.innerHeight - dock - Math.max(top, 0) - BOTTOM_MARGIN - ROW_TITLE_HEIGHT * counts.length;
    const across = (count: number) => (box.width - gap * (count - 1)) / (count * CARD_WIDTH);
    const most = Math.max(...counts);
    const longest = Math.min(across(most), height / counts.length / CARD_HEIGHT, MAX_ZOOM);
    const left = (height - longest * CARD_HEIGHT) / Math.max(counts.length - 1, 1) / CARD_HEIGHT;
    const best = counts[row] === most ? longest : Math.min(across(counts[row]), left, MAX_ZOOM);
    return Math.floor(Math.max(best, MIN_ROW_ZOOM) * 100) / 100;
  };
  return useZoom(ref, fit, `${counts.join(",")}/${row}/${gap}`);
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
