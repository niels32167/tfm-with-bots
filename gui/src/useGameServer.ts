import { useCallback, useEffect, useRef, useState } from "react";

import { downloadReplayFile, readReplayFile } from "./replayFiles";
import type { ClientMessage, NewGameSettings, ServerMessage, Update } from "./types";

/** The server's latest update: Controllers, seed, Player View and Decision (the log is kept apart). */
export type GameUpdate = Omit<Update, "type" | "log_start" | "log">;

/** The connection to the local server, and the latest Game state it sent. */
export function useGameServer() {
  const [connected, setConnected] = useState(false);
  const [game, setGame] = useState<GameUpdate | null>(null);
  const [log, setLog] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  // The Decision a pick was sent for, so its buttons stay disabled until the server answers.
  const [pickedSequence, setPickedSequence] = useState<number | null>(null);
  const socket = useRef<WebSocket | null>(null);

  useEffect(() => {
    let stopped = false;
    let retry: number | undefined;

    function connect() {
      const protocol = window.location.protocol === "https:" ? "wss" : "ws";
      const ws = new WebSocket(`${protocol}://${window.location.host}/ws`);
      socket.current = ws;
      // Events from a socket that has since been replaced (say, by React's dev-mode
      // double mount) must not touch the state.
      const isCurrent = () => socket.current === ws;
      ws.onopen = () => {
        if (!isCurrent()) return;
        // The server sends the current Game straight away, if it has one. Whatever
        // was shown before belongs to a connection (maybe a server) that is gone.
        setGame(null);
        setLog([]);
        setError(null);
        setPickedSequence(null);
        setConnected(true);
      };
      ws.onclose = () => {
        if (!isCurrent()) return;
        setConnected(false);
        if (!stopped) retry = window.setTimeout(connect, 1000);
      };
      ws.onmessage = (event) => isCurrent() && receive(JSON.parse(event.data) as ServerMessage);
    }

    function receive(message: ServerMessage) {
      switch (message.type) {
        case "update": {
          const { type: _type, log_start, log: lines, ...state } = message;
          setGame(state);
          setLog((previous) => [...previous.slice(0, log_start), ...lines]);
          setError(null);
          setPickedSequence(null);
          break;
        }
        case "game_over":
          // The final scores also arrive in the view; nothing more to do.
          break;
        case "replay_file":
          downloadReplayFile(message.file);
          break;
        case "error":
          setError(message.message);
          setPickedSequence(null);
          break;
      }
    }

    connect();
    return () => {
      stopped = true;
      window.clearTimeout(retry);
      socket.current?.close();
    };
  }, []);

  const send = useCallback((message: ClientMessage) => {
    socket.current?.send(JSON.stringify(message));
  }, []);

  const newGame = useCallback(
    (settings: NewGameSettings) => send({ type: "new_game", ...settings }),
    [send],
  );

  const pick = useCallback(
    (sequence: number, index: number) => {
      setPickedSequence(sequence);
      send({ type: "pick", sequence, index });
    },
    [send],
  );

  const undo = useCallback(() => send({ type: "undo" }), [send]);

  /** The server answers with the Replay file, which is then downloaded. */
  const saveReplay = useCallback(() => send({ type: "save_replay" }), [send]);

  const loadReplay = useCallback(
    async (file: File, botDelay: number) => {
      try {
        send({ type: "load_replay", file: await readReplayFile(file), bot_delay: botDelay });
      } catch (problem) {
        setError((problem as Error).message);
      }
    },
    [send],
  );

  const clearError = useCallback(() => setError(null), []);

  const setBotDelay = useCallback(
    (botDelay: number) => send({ type: "set_bot_delay", bot_delay: botDelay }),
    [send],
  );

  return {
    connected,
    game,
    log,
    error,
    clearError,
    pickedSequence,
    newGame,
    pick,
    undo,
    saveReplay,
    loadReplay,
    setBotDelay,
  };
}
