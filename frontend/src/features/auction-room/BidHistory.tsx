import { Link } from "react-router";

import type { Bid } from "../../types/bid";
import { formatClock } from "../../utils/dates";
import { shortHash } from "../../utils/lots";
import { formatCents } from "../../utils/money";

type BidHistoryProps = {
  lotId: string;
  bids: Bid[];
  viewerAlias: string | null;
};

/** Os lances mais recentes, com o começo do hash de cada um para conferir na auditoria. */
export function BidHistory({ lotId, bids, viewerAlias }: BidHistoryProps) {
  return (
    <section className="flex flex-col gap-3">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="font-serif text-[22px] font-semibold">Histórico de lances</h2>
        <Link to={`/auditoria/${lotId}`} className="text-sm font-semibold text-gold-dark hover:text-ink">
          Auditar este lote
        </Link>
      </div>

      {bids.length === 0 ? (
        <p className="rounded-md border border-line bg-surface px-6 py-8 text-center text-muted">
          Nenhum lance ainda.
        </p>
      ) : (
        <div className="overflow-x-auto rounded-md border border-line bg-surface">
          <table className="w-full min-w-130 border-collapse text-left text-[15px]">
            <thead>
              <tr className="border-b border-line text-[13px] text-muted">
                <th scope="col" className="px-4 py-3 font-semibold">#</th>
                <th scope="col" className="px-4 py-3 font-semibold">Licitante</th>
                <th scope="col" className="px-4 py-3 text-right font-semibold">Valor</th>
                <th scope="col" className="px-4 py-3 font-semibold">Horário</th>
                <th scope="col" className="px-4 py-3 font-semibold">Hash</th>
              </tr>
            </thead>
            <tbody>
              {bids.map((bid) => {
                const isMine = viewerAlias !== null && bid.bidder_alias === viewerAlias;
                return (
                  <tr key={bid.sequence} className="border-b border-line last:border-b-0">
                    <td className="px-4 py-3 font-mono text-muted">{bid.sequence}</td>
                    <td className={`px-4 py-3 ${isMine ? "font-semibold" : ""}`}>{isMine ? "Você" : bid.bidder_alias}</td>
                    <td className="px-4 py-3 text-right font-mono whitespace-nowrap">{formatCents(bid.amount)}</td>
                    <td className="px-4 py-3 font-mono text-sm whitespace-nowrap">{formatClock(bid.created_at)}</td>
                    <td className="px-4 py-3 font-mono text-sm text-muted" title={bid.hash}>{shortHash(bid.hash)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
