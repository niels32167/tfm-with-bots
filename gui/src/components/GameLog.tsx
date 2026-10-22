/** The game log, newest line first as on Board Game Arena. */
export function GameLog({ log }: { log: string[] }) {
  return (
    <section className="game-log" aria-label="Game log">
      <h2>Game log</h2>
      <ol reversed className="game-log-lines">
        {log
          .map((line, index) => (
            <li key={index} className={line.startsWith("Generation") ? "generation-line" : ""}>
              {line}
            </li>
          ))
          .reverse()}
      </ol>
    </section>
  );
}
