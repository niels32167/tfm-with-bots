import { useRef } from "react";

interface Props {
  className: string;
  onLoad: (file: File) => void;
}

/** A button that asks for a Replay file and hands it over. */
export function LoadReplayButton({ className, onLoad }: Props) {
  const input = useRef<HTMLInputElement>(null);
  return (
    <>
      <button className={className} onClick={() => input.current?.click()}>
        Load Replay…
      </button>
      <input
        ref={input}
        type="file"
        accept=".json,application/json"
        hidden
        onChange={(event) => {
          const file = event.target.files?.[0];
          // Clear the choice, so picking the same file again still loads it.
          event.target.value = "";
          if (file) onLoad(file);
        }}
      />
    </>
  );
}
