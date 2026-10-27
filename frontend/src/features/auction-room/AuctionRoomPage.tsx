import { useEffect, useState } from "react";
import { Link, useParams } from "react-router";

import { Countdown } from "../../components/Countdown";
import { useAuth } from "../../hooks/useAuth";
import { useLotSocket } from "../../hooks/useLotSocket";
import { useNow } from "../../hooks/useNow";
import { ApiError } from "../../services/api";
import { fetchLot } from "../../services/lots";
import { fetchWallet } from "../../services/wallet";
import type { PlacedBid } from "../../types/bid";
import type { Lot } from "../../types/lot";
import { formatClock, formatDayTime } from "../../utils/dates";
import { bidsLabel, bookByline, currentPhase, lotPrice, lotStatus } from "../../utils/lots";
import { formatCents } from "../../utils/money";
import { BidForm } from "./BidForm";
import { BidHistory } from "./BidHistory";
import { LotDetails } from "./LotDetails";
import { LotResult } from "./LotResult";
import { RoomStatus } from "./RoomStatus";

type Fetched = { lot: Lot | null; missing: boolean };

/** A rota /lotes/:lotId. A chave recria a sala do zero quando a pessoa vai de um lote a outro. */
export function AuctionRoomPage() {
  const { lotId = "" } = useParams();
  return <LotRoom key={lotId} lotId={lotId} />;
}

function LotRoom({ lotId }: { lotId: string }) {
  const { user, isLoading } = useAuth();
  const { room, applyPlacedBid, applyFetchedLot } = useLotSocket(lotId, {
    enabled: !isLoading,
    identify: Boolean(user),
  });
  const now = useNow() + room.offsetMs;

  // O GET mostra o lote antes do primeiro snapshot e responde 404 para um lote que não existe.
  const [fetched, setFetched] = useState<Fetched>({ lot: null, missing: false });
  useEffect(() => {
    const controller = new AbortController();
    fetchLot(lotId, controller.signal)
      .then((lot) => {
        if (!controller.signal.aborted) setFetched({ lot, missing: false });
      })
      .catch((error) => {
        if (!controller.signal.aborted && error instanceof ApiError && error.status === 404) {
          setFetched({ lot: null, missing: true });
        }
      });
    return () => controller.abort();
  }, [lotId]);

  // O disponível muda quando a pessoa dá um lance e quando alguém cobre o lance dela.
  const isBidder = user?.role === "BIDDER";
  const [walletVersion, setWalletVersion] = useState(0);
  const [available, setAvailable] = useState<number | null>(null);
  useEffect(() => {
    if (!isBidder) return;
    const controller = new AbortController();
    fetchWallet(controller.signal)
      .then((wallet) => {
        if (!controller.signal.aborted) setAvailable(wallet.available);
      })
      .catch(() => {
        // Sem a carteira, o formulário mostra "–" no disponível; o lance continua possível.
      });
    return () => controller.abort();
  }, [isBidder, walletVersion, room.outbid]);

  function handlePlaced(placed: PlacedBid) {
    applyPlacedBid(placed);
    setWalletVersion((current) => current + 1);
  }

  // Quando a contagem chega a zero, busca o lote uma vez: o GET liquida o lote e o servidor
  // avisa a sala com "lot.closed". Se o anti-sniping estendeu o fim, o lote volta ao vivo
  // com o novo ends_at, e a busca só acontece de novo quando esse novo fim chegar.
  const loaded = room.lot ?? fetched.lot;
  const endedAt = loaded && currentPhase(loaded, now) === "ENDED" ? loaded.ends_at : null;
  useEffect(() => {
    if (!endedAt) return;
    const controller = new AbortController();
    fetchLot(lotId, controller.signal)
      .then((fresh) => {
        if (!controller.signal.aborted) applyFetchedLot(fresh);
      })
      .catch(() => {
        // Sem resposta, o "lot.closed" do WebSocket ainda atualiza a sala.
      });
    return () => controller.abort();
  }, [lotId, endedAt, applyFetchedLot]);

  if (room.notFound || fetched.missing) {
    return (
      <section className="flex flex-col items-start gap-3">
        <h1 className="font-serif text-4xl font-bold">Lote não encontrado</h1>
        <p className="text-muted">O endereço pode estar errado, ou o lote não existe mais.</p>
        <Link to="/" className="font-semibold text-gold-dark hover:text-ink">Voltar à vitrine</Link>
      </section>
    );
  }

  if (!loaded) {
    return <p className="rounded-md border border-line bg-surface px-6 py-10 text-center text-muted">Carregando a sala…</p>;
  }

  const lot: Lot = { ...loaded, phase: currentPhase(loaded, now) };
  const status = lotStatus(lot);
  const isLive = lot.phase === "LIVE";
  const isUpcoming = lot.phase === "SCHEDULED";
  const viewerAlias = room.viewerAlias ?? user?.public_alias ?? null;
  const isLeader = viewerAlias !== null && lot.leader_alias === viewerAlias;
  const hasBidHere = viewerAlias !== null && room.bids.some((bid) => bid.bidder_alias === viewerAlias);
  const isExtended = room.extended || Date.parse(lot.ends_at) !== Date.parse(lot.original_ends_at);

  return (
    <div className="grid items-start gap-10 lg:grid-cols-[340px_minmax(0,1fr)]">
      <LotDetails lot={lot} />

      <div className="flex min-w-0 flex-col gap-6">
        <div className="flex flex-col gap-2">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <span className={`inline-flex items-center gap-1.75 text-xs font-semibold tracking-[0.08em] uppercase ${status.text}`}>
              <span aria-hidden="true" className={`size-2 rounded-full ${status.dot} ${isLive ? "animate-pulse" : ""}`} />
              {status.label}
            </span>
            {room.connection !== "open" && (
              <span className="text-[13px] text-muted">
                {room.connection === "connecting" ? "Conectando à sala…" : "Conexão perdida. Reconectando…"}
              </span>
            )}
          </div>
          <h1 className="font-serif text-[40px] leading-tight font-bold">{lot.title}</h1>
          <p className="text-muted">{bookByline(lot)}</p>
        </div>

        <RoomStatus lot={lot} viewerAlias={viewerAlias} outbid={room.outbid || hasBidHere} cancelReason={room.cancelReason} />

        <div className="grid grid-cols-[repeat(auto-fit,minmax(220px,1fr))] gap-4">
          <div className="flex flex-col gap-1 rounded-md border border-gold bg-gold-soft px-5 py-4.5">
            <span className="text-[13px] text-muted">
              {lot.current_price === null ? "Lance inicial" : isLive ? "Lance atual" : "Último lance"}
            </span>
            <span className="font-mono text-[32px] font-medium">{formatCents(lotPrice(lot))}</span>
            <span className="text-[13px] text-muted">
              {bidsLabel(lot.bid_count)}
              {lot.leader_alias && ` · lidera ${isLeader ? "você" : lot.leader_alias}`}
            </span>
          </div>

          <div className="flex flex-col gap-1 rounded-md border border-line bg-surface px-5 py-4.5">
            <span className="text-[13px] text-muted">
              {isLive ? "Termina em" : isUpcoming ? "Abre em" : "Encerrado em"}
            </span>
            <span className="text-[32px] font-medium">
              {isLive && <Countdown endsAt={lot.ends_at} offsetMs={room.offsetMs} />}
              {isUpcoming && <Countdown endsAt={lot.starts_at} offsetMs={room.offsetMs} />}
              {!isLive && !isUpcoming && formatDayTime(lot.closed_at ?? lot.ends_at)}
            </span>
            <p role="status" className="text-[13px] font-semibold text-gold-dark">
              {isLive && isExtended && `Lote prorrogado · novo fim às ${formatClock(lot.ends_at)}`}
            </p>
          </div>
        </div>

        {(isLive || isUpcoming) && !user && (
          <div className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-line bg-surface p-5">
            <p className="text-[15px]">Você está assistindo como visitante. Entre na sua conta para dar lances.</p>
            <Link to="/entrar"
              className="flex h-11 items-center rounded-md bg-gold-dark px-5 text-[15px] font-semibold text-paper hover:opacity-90">
              Entrar para dar lances
            </Link>
          </div>
        )}
        {(isLive || isUpcoming) && user?.role === "AUCTIONEER" && (
          <p className="rounded-md border border-line bg-surface p-5 text-[15px] text-muted">
            Você está assistindo como leiloeiro. Leiloeiros acompanham a sala, mas não dão lances.
          </p>
        )}
        {(isLive || isUpcoming) && isBidder && (
          <BidForm lot={lot} isOpen={isLive} available={available} onPlaced={handlePlaced} />
        )}
        {/* Fica sempre na página para o leitor de tela anunciar quando o lote é liquidado. */}
        <div role="status" aria-live="polite">
          {lot.phase === "CLOSED" && <LotResult lot={lot} viewerAlias={viewerAlias} />}
        </div>

        <BidHistory lotId={lot.id} bids={room.bids} viewerAlias={viewerAlias} />
      </div>
    </div>
  );
}
