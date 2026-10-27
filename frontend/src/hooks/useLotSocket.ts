/**
 * A conexão ao vivo com a sala de um lote.
 *
 * Abre o WebSocket (com um ticket novo a cada conexão, para quem está logado),
 * guarda o estado da sala a partir dos eventos e reconecta sozinho quando a conexão cai.
 */

import { useCallback, useEffect, useReducer } from "react";

import { withQuery } from "../services/api";
import { fetchWsTicket } from "../services/auth";
import type { Bid, PlacedBid, RoomEvent } from "../types/bid";
import type { Lot } from "../types/lot";

/** O código com que o backend fecha a conexão de um lote que não existe. */
const LOT_NOT_FOUND = 4404;
const RECENT_BIDS = 20;
const FIRST_RETRY_MS = 1000;
const MAX_RETRY_MS = 30_000;

export type ConnectionStatus = "connecting" | "open" | "reconnecting";

export type RoomState = {
  lot: Lot | null;
  /** Os lances mais recentes primeiro, como no snapshot. */
  bids: Bid[];
  /** O apelido de quem assiste, ou null para visitantes. */
  viewerAlias: string | null;
  /** server_now − Date.now() do último evento, para a contagem seguir o relógio do servidor. */
  offsetMs: number;
  /** Verdadeiro depois que a pessoa perde a liderança; volta a falso quando ela lidera de novo. */
  outbid: boolean;
  /** Verdadeiro depois de um lot.extended recebido nesta conexão. */
  extended: boolean;
  cancelReason: string | null;
  connection: ConnectionStatus;
  notFound: boolean;
};

type Action =
  | { type: "event"; event: RoomEvent; offsetMs: number }
  | { type: "placed"; placed: PlacedBid }
  | { type: "fetched"; lot: Lot }
  | { type: "connection"; status: ConnectionStatus }
  | { type: "not-found" };

const INITIAL_STATE: RoomState = {
  lot: null,
  bids: [],
  viewerAlias: null,
  offsetMs: 0,
  outbid: false,
  extended: false,
  cancelReason: null,
  connection: "connecting",
  notFound: false,
};

/** Junta um lance à lista, sem repetir (ele chega pela resposta do POST e pelo WebSocket). */
function addBid(bids: Bid[], bid: Bid): Bid[] {
  if (bids.some((existing) => existing.sequence === bid.sequence)) return bids;
  return [bid, ...bids].sort((a, b) => b.sequence - a.sequence).slice(0, RECENT_BIDS);
}

/** Um lote mais novo substitui o atual; um que chegou atrasado (menos lances) é ignorado. */
function newerLot(current: Lot | null, next: Lot): Lot {
  return current && next.bid_count < current.bid_count ? current : next;
}

/** O lote mudou de líder: a pessoa foi superada se liderava antes e não lidera mais. */
function withLeader(state: RoomState, lot: Lot): RoomState {
  const alias = state.viewerAlias;
  const wasLeader = alias !== null && state.lot?.leader_alias === alias;
  const isLeader = alias !== null && lot.leader_alias === alias;
  return { ...state, lot, outbid: isLeader ? false : state.outbid || wasLeader };
}

function applyEvent(state: RoomState, event: RoomEvent): RoomState {
  switch (event.type) {
    case "lot.snapshot": {
      // Um snapshot (inclusive o de uma reconexão) substitui todo o estado da sala.
      const viewerAlias = event.viewer?.alias ?? null;
      const base = { ...state, viewerAlias, bids: event.bids, extended: false, cancelReason: null };
      return withLeader(base, event.lot);
    }
    case "bid.accepted":
      return withLeader({ ...state, bids: addBid(state.bids, event.bid) }, newerLot(state.lot, event.lot));
    case "lot.extended":
      if (!state.lot) return state;
      return {
        ...state,
        extended: true,
        lot: { ...state.lot, ends_at: event.ends_at, original_ends_at: event.original_ends_at },
      };
    case "lot.cancelled":
      return { ...state, lot: event.lot, cancelReason: event.reason };
    case "lot.closed":
      // O lote liquidado já traz o vencedor (winner_alias) e o preço final (final_price).
      return { ...state, lot: event.lot };
    case "user.outbid":
      return { ...state, outbid: true };
  }
}

function reducer(state: RoomState, action: Action): RoomState {
  switch (action.type) {
    case "event":
      return { ...applyEvent(state, action.event), offsetMs: action.offsetMs };
    case "placed": {
      const { bid, lot, extended } = action.placed;
      const next = withLeader({ ...state, bids: addBid(state.bids, bid) }, newerLot(state.lot, lot));
      return extended ? { ...next, extended: true } : next;
    }
    case "fetched":
      return withLeader(state, newerLot(state.lot, action.lot));
    case "connection":
      return { ...state, connection: action.status };
    case "not-found":
      return { ...state, notFound: true };
  }
}

/**
 * O começo do endereço do WebSocket. Em produção, VITE_WS_URL aponta direto para o Render
 * (a Vercel não repassa WebSocket). Sem ela, no desenvolvimento, usa a própria página (o proxy do Vite).
 */
function socketBase(): string {
  const configured = import.meta.env.VITE_WS_URL;
  if (configured) return configured.replace(/\/+$/, "");
  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  return `${protocol}://${window.location.host}`;
}

function socketUrl(lotId: string, ticket: string | null): string {
  return withQuery(`${socketBase()}/ws/lots/${lotId}/`, { ticket: ticket ?? undefined });
}

type Options = {
  /** Só conecta quando a sessão já foi conferida, para não abrir como visitante e reabrir logado. */
  enabled: boolean;
  /** Pede um ticket para se identificar (quem está logado). */
  identify: boolean;
};

export function useLotSocket(lotId: string, { enabled, identify }: Options) {
  const [state, dispatch] = useReducer(reducer, INITIAL_STATE);

  useEffect(() => {
    if (!enabled) return;

    let socket: WebSocket | null = null;
    let retryTimer: ReturnType<typeof setTimeout> | undefined;
    let attempt = 0;
    let stopped = false;

    async function connect() {
      // O ticket é de uso único: cada conexão, inclusive as reconexões, pede um novo.
      let ticket: string | null = null;
      if (identify) {
        try {
          ticket = (await fetchWsTicket()).ticket;
        } catch {
          // Sem ticket, a pessoa ainda assiste à sala como visitante.
        }
      }
      if (stopped) return;

      const current = new WebSocket(socketUrl(lotId, ticket));
      socket = current;

      current.onopen = () => {
        attempt = 0;
        dispatch({ type: "connection", status: "open" });
      };

      current.onmessage = (message: MessageEvent<string>) => {
        let event: RoomEvent;
        try {
          event = JSON.parse(message.data) as RoomEvent;
        } catch {
          return;
        }
        const offsetMs = Date.parse(event.server_now) - Date.now();
        dispatch({ type: "event", event, offsetMs: Number.isNaN(offsetMs) ? 0 : offsetMs });
      };

      current.onclose = (closed) => {
        socket = null;
        if (stopped) return;
        if (closed.code === LOT_NOT_FOUND) {
          dispatch({ type: "not-found" });
          return;
        }
        // Espera crescente: 1 s, 2 s, 4 s... até 30 s entre as tentativas.
        dispatch({ type: "connection", status: "reconnecting" });
        const delay = Math.min(FIRST_RETRY_MS * 2 ** attempt, MAX_RETRY_MS);
        attempt += 1;
        retryTimer = setTimeout(connect, delay);
      };
    }

    connect();

    return () => {
      stopped = true;
      clearTimeout(retryTimer);
      socket?.close();
    };
  }, [lotId, enabled, identify]);

  /** Mostra na hora o lance que a própria pessoa acabou de dar, sem esperar o WebSocket. */
  const applyPlacedBid = useCallback((placed: PlacedBid) => dispatch({ type: "placed", placed }), []);

  /** Usa o lote buscado pela API (GET), para quando o WebSocket não trouxer a novidade. */
  const applyFetchedLot = useCallback((lot: Lot) => dispatch({ type: "fetched", lot }), []);

  return { room: state, applyPlacedBid, applyFetchedLot };
}
