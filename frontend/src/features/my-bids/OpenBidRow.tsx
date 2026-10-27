import { Link } from "react-router";

import { Countdown } from "../../components/Countdown";
import { LotCover } from "../../components/LotCover";
import { useNow } from "../../hooks/useNow";
import type { MyOpenBid } from "../../types/myBids";
import { formatDayTime } from "../../utils/dates";
import { currentPhase, lotPrice } from "../../utils/lots";
import { formatCents } from "../../utils/money";

/** Uma linha da aba "Lotes com lance": como está o lote e como a pessoa está nele. */
export function OpenBidRow({ item }: { item: MyOpenBid }) {
  const { lot } = item;
  const now = useNow();
  const phase = currentPhase(lot, now);

  return (
    <li className="flex flex-wrap items-center gap-x-6 gap-y-4 rounded-md border border-line bg-surface p-4">
      <div className="flex min-w-0 flex-[1_1_260px] items-center gap-3.5">
        <LotCover title={lot.title} authors={lot.authors} coverUrl={lot.cover_url} size="thumb" />
        <div className="flex min-w-0 flex-col gap-0.5">
          <h2 className="font-serif text-lg leading-tight font-semibold">{lot.title}</h2>
          <p className="text-[13px] text-muted">
            {phase === "LIVE" && (
              <>
                <span className="font-semibold text-live">Ao vivo</span> · termina em <Countdown endsAt={lot.ends_at} />
              </>
            )}
            {phase === "SCHEDULED" && `Começa em ${formatDayTime(lot.starts_at)}`}
            {phase === "ENDED" && "Encerrado · aguardando liquidação"}
          </p>
        </div>
      </div>

      <dl className="flex gap-6">
        <div className="flex flex-col">
          <dt className="text-[13px] text-muted">Seu maior lance</dt>
          <dd className="font-mono">{formatCents(item.my_max_bid)}</dd>
        </div>
        <div className="flex flex-col">
          <dt className="text-[13px] text-muted">Lance atual</dt>
          <dd className="font-mono">{formatCents(lotPrice(lot))}</dd>
        </div>
      </dl>

      {item.winning ? (
        <span className="rounded-full border border-green bg-green-soft px-3 py-1 text-[13px] font-semibold whitespace-nowrap text-green">
          Você está ganhando
        </span>
      ) : (
        <span className="rounded-full border border-red bg-red-soft px-3 py-1 text-[13px] font-semibold whitespace-nowrap text-red">
          Você foi superado
        </span>
      )}

      <Link to={`/lotes/${lot.id}`}
        className="ml-auto flex h-10 items-center rounded-md border border-line px-4 text-sm font-semibold whitespace-nowrap hover:bg-paper">
        Ir para a sala
      </Link>
    </li>
  );
}
