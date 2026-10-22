import type { ReplayFile } from "./types";

/** Saves a Replay file through the browser's download, named after its seed and length. */
export function downloadReplayFile(file: ReplayFile) {
  const start = file.replay.start;
  const seed = "settings" in start ? start.settings.seed : start.scenario.seed;
  const blob = new Blob([JSON.stringify(file, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `terraforming-mars-seed-${seed}-pick-${file.replay.picks.length}.json`;
  link.click();
  // Give the browser time to start the download before the file's address goes away.
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

/** The contents of a file the user picked. The server checks that it really is a Replay file. */
export async function readReplayFile(file: File): Promise<unknown> {
  try {
    return JSON.parse(await file.text());
  } catch {
    throw new Error(`${file.name} is not a Replay file: it isn't JSON.`);
  }
}
