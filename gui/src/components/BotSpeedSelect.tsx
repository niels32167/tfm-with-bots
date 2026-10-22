export const DEFAULT_BOT_DELAY = 0.8;

/** How long each Random Bot waits before picking, in seconds. */
const BOT_SPEEDS = [
  { label: "Instant", delay: 0 },
  { label: "Fast", delay: 0.3 },
  { label: "Normal", delay: DEFAULT_BOT_DELAY },
  { label: "Slow", delay: 1.6 },
];

interface Props {
  delay: number;
  onChange: (delay: number) => void;
}

/** A choice of Random Bot speeds. */
export function BotSpeedSelect({ delay, onChange }: Props) {
  const known = BOT_SPEEDS.some((speed) => speed.delay === delay);
  return (
    <label className="bot-speed">
      Random Bot speed{" "}
      <select value={delay} onChange={(event) => onChange(Number(event.target.value))}>
        {BOT_SPEEDS.map((speed) => (
          <option key={speed.delay} value={speed.delay}>
            {speed.label} ({speed.delay} s)
          </option>
        ))}
        {!known && <option value={delay}>Custom ({delay} s)</option>}
      </select>
    </label>
  );
}
