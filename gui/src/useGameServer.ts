import { useCallback, useEffect, useRef, useState } from "react";

import { downloadReplayFile, readReplayFile } from "./replayFiles";
import type {
  Card,
  ClientMessage,
  ControllerName,
  ControllerOnOffer,
  DevView,
  NewGameSettings,
  Scenario,
  ServerMessage,
  Update,
} from "./types";

/** The server's latest update: Controllers, seed, Player View and Decision (the log is kept apart). */
export type GameUpdate = Omit<Update, "type" | "log_start" | "log">;

// The shape of a visitor id, which the server checks.
const VISITOR_ID = /^[A-Za-z0-9-]{8,64}$/;
const VISITOR_KEY = "terraforming-mars-visitor";

/** This browser's visitor id, kept so that a hosted server finds this visitor's Game again after a reload. The
 * local server ignores it. Without storage (a private window, say) it lasts as long as the page. */
function visitorId(): string {
  const fresh =
    typeof crypto.randomUUID === "function"
      ? crypto.randomUUID()
      : Array.from(crypto.getRandomValues(new Uint8Array(16)), (byte) => byte.toString(16).padStart(2, "0")).join("");
  try {
    const kept = window.localStorage.getItem(VISITOR_KEY);
    if (kept && VISITOR_ID.test(kept)) return kept;
    window.localStorage.setItem(VISITOR_KEY, fresh);
  } catch {
    // Storage may be blocked; the id made here then serves this page alone.
  }
  return fresh;
}

/** The connection to the server, the card catalog, the Controllers on offer, and the latest Game state it
 * sent. */
export function useGameServer() {
  const [connected, setConnected] = useState(false);
  // Every card's printed data, which the server sends first on each connection.
  const [cards, setCards] = useState<Card[]>([]);
  // A human and the registered Controllers, which the server sends next.
  const [controllers, setControllers] = useState<ControllerOnOffer[]>([]);
  // Whether the server is hosted for anyone with its link, as it says with the Controllers.
  const [hosted, setHosted] = useState(false);
  const [game, setGame] = useState<GameUpdate | null>(null);
  const [log, setLog] = useState<string[]>([]);
  // What the dev panel last asked to see.
  const [devView, setDevView] = useState<DevView | null>(null);
  const [error, setError] = useState<string | null>(null);
  // The Decision a pick was sent for, so its buttons stay disabled until the server answers.
  const [pickedSequence, setPickedSequence] = useState<number | null>(null);
  const socket = useRef<WebSocket | null>(null);

  useEffect(() => {
    let stopped = false;
    let retry: number | undefined;
    const visitor = visitorId();

    function connect() {
      const protocol = window.location.protocol === "https:" ? "wss" : "ws";
      const ws = new WebSocket(`${protocol}://${window.location.host}/ws?visitor=${visitor}`);
      socket.current = ws;
      // Events from a socket that has since been replaced (say, by React's dev-mode
      // double mount) must not touch the state.
      const isCurrent = () => socket.current === ws;
      // Whether the server welcomed this connection with the card catalog. A hosted server that turns it away
      // (when full) sends an error instead and closes it, and the error stays on the splash screen meanwhile.
      let welcomed = false;
      ws.onclose = () => {
        if (!isCurrent()) return;
        setConnected(false);
        // An error from a Game that was going on belongs to that Game, not to the splash screen.
        if (welcomed) setError(null);
        if (!stopped) retry = window.setTimeout(connect, 1000);
      };
      ws.onmessage = (event) => {
        if (!isCurrent()) return;
        const message = JSON.parse(event.data) as ServerMessage;
        if (message.type === "card_catalog") {
          welcomed = true;
          // The server sends the current Game straight after, if it has one. Whatever was shown before belongs
          // to a connection (maybe a server) that is gone.
          setGame(null);
          setLog([]);
          setDevView(null);
          setPickedSequence(null);
          setError(null);
          setConnected(true);
        }
        receive(message);
      };
    }

    function receive(message: ServerMessage) {
      switch (message.type) {
        case "card_catalog":
          setCards(message.cards);
          break;
        case "controllers":
          setControllers(message.controllers);
          setHosted(message.hosted);
          break;
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
        case "dev_view": {
          const { type: _type, ...shown } = message;
          setDevView(shown);
          break;
        }
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

  /** A Replay file of the position alone is what starts a Game from a Scenario. */
  const startFromScenario = useCallback(
    (scenario: Scenario, controllers: ControllerName[], botDelay: number) =>
      send({
        type: "load_replay",
        file: { controllers, replay: { start: { scenario }, picks: [] } },
        bot_delay: botDelay,
      }),
    [send],
  );

  /** The server answers only this GUI, with `step` or else the latest one; the Game doesn't change. */
  const askForDevView = useCallback(
    (step: number | null) => send(step === null ? { type: "dev_view" } : { type: "dev_view", step }),
    [send],
  );

  const clearError = useCallback(() => setError(null), []);

  const setBotDelay = useCallback(
    (botDelay: number) => send({ type: "set_bot_delay", bot_delay: botDelay }),
    [send],
  );

  return {
    connected,
    cards,
    controllers,
    hosted,
    game,
    log,
    devView,
    error,
    clearError,
    pickedSequence,
    newGame,
    pick,
    undo,
    saveReplay,
    loadReplay,
    startFromScenario,
    askForDevView,
    setBotDelay,
  };
}
