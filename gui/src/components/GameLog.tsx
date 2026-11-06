import { PLAYER_COLOURS } from "../players";

interface Props {
  log: string[];
  /** The Players' names, by index: in the log they are bold, in their colour. */
  players?: string[];
}

/** The game log, newest line first as on Board Game Arena. */
export function GameLog({ log, players = [] }: Props) {
  return (
    <section className="game-log" aria-label="Game log">
      <h2>Game log</h2>
      <ol reversed className="game-log-lines">
        {log
          .map((line, index) => (
            <li key={index} className={line.startsWith("Generation") ? "generation-line" : ""}>
              <LogLine line={line} players={players} />
            </li>
          ))
          .reverse()}
      </ol>
    </section>
  );
}

/** One line, with each Player's name in their colour. */
export function LogLine({ line, players }: { line: string; players: string[] }) {
  if (players.length === 0) return <>{line}</>;
  const names = new RegExp(`(${players.map((name) => name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|")})`);
  return (
    <>
      {line.split(names).map((part, index) => {
        const player = players.indexOf(part);
        return player < 0 ? (
          part
        ) : (
          <strong key={index} className="log-player" style={{ color: PLAYER_COLOURS[player] }}>
            {part}
          </strong>
        );
      })}
    </>
  );
}
