import { Link } from "react-router";

import { Countdown } from "../../components/Countdown";
import { LotCover } from "../../components/LotCover";
import type { Lot } from "../../types/lot";
import { formatDayTime } from "../../utils/dates";
import { bidsLabel, bookByline, lotStatus } from "../../utils/lots";
import { formatCents } from "../../utils/money";


function priceOf(lot: Lot): { label: string; cents: number } {
  if (lot.phase === "CLOSED" && lot.final_price !== null) {
    return { label: "Arrematado por", cents: lot.final_price };
  }
  if (lot.current_price !== null) {
    return { label: lot.phase === "LIVE" ? "Lance atual" : "Último lance", cents: lot.current_price };
  }
  return { label: "Lance inicial", cents: lot.starting_price };
}


type LotCardProps = {
  lot: Lot;
  isVisitor: boolean;
};

export function LotCard({ lot, isVisitor }: LotCardProps) {
  const status = lotStatus(lot);
  const price = priceOf(lot);
  const isLive = lot.phase === "LIVE";

  const byline = isLive ? `${bookByline(lot)} · ${bidsLabel(lot.bid_count)}` : bookByline(lot);

  return (
    <article className="flex flex-col overflow-hidden rounded-md border border-line bg-surface">
      <div className="flex h-62 items-center justify-center border-b border-line bg-paper">
        <LotCover title={lot.title} authors={lot.authors} coverUrl={lot.cover_url} />
      </div>

      <div className="flex flex-1 flex-col gap-2 p-4.5">
        <span
          className={`inline-flex items-center gap-1.75 text-xs font-semibold tracking-[0.08em] uppercase ${status.text}`}
        >
          <span aria-hidden="true" className={`size-2 rounded-full ${status.dot}`} />
          {status.label}
        </span>
        <h2 className="font-serif text-[21px] leading-tight font-semibold">{lot.title}</h2>
        <p className="text-sm text-muted">{byline}</p>

        <div className="mt-auto flex flex-wrap items-end justify-between gap-x-3 gap-y-1 border-t border-line pt-3.5">
          <div className="flex flex-col gap-0.5">
            <span className="text-xs text-muted">{price.label}</span>
            <span className="font-mono text-[19px] font-medium">{formatCents(price.cents)}</span>
          </div>
          <span className={`text-[13px] whitespace-nowrap ${isLive ? "text-ink" : "text-muted"}`}>
            {isLive && (
              <>
                termina em <Countdown endsAt={lot.ends_at} />
              </>
            )}
            {lot.phase === "SCHEDULED" && `abre ${formatDayTime(lot.starts_at)}`}
            {!isLive && lot.phase !== "SCHEDULED" && bidsLabel(lot.bid_count)}
          </span>
        </div>

        <Link
          to={`/lotes/${lot.id}`}
          className={
            isLive
              ? "mt-2 flex h-11 items-center justify-center rounded-md bg-gold-dark font-semibold text-paper hover:opacity-90"
              : "mt-2 flex h-11 items-center justify-center rounded-md border border-line font-semibold text-ink hover:bg-paper"
          }
        >
          {isLive ? (isVisitor ? "Assistir ao vivo" : "Entrar na sala") : "Ver detalhes"}
        </Link>
        <Link
          to={`/auditoria/${lot.id}`}
          className="flex min-h-11 items-center justify-center gap-1.5 text-sm font-semibold text-gold-dark hover:text-ink"
        >
          <svg aria-hidden="true" width="16" height="16" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 3l7 3v5c0 4.5-3 8.3-7 10-4-1.7-7-5.5-7-10V6z" />
            <path d="M9 12l2 2 4-4" />
          </svg>
          Auditar histórico
        </Link>
      </div>
    </article>
  );
}
