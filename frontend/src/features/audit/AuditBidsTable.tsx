import type { AuditBid } from "../../types/audit";
import { abbreviateHash } from "../../utils/audit";
import { formatUtc } from "../../utils/dates";
import { formatCents } from "../../utils/money";

/** Todos os lances do lote, com os hashes que formam a cadeia. A linha com problema fica vermelha. */
export function AuditBidsTable({ bids }: { bids: AuditBid[] }) {
  return (
    <section className="flex flex-col overflow-hidden rounded-md border border-line bg-surface">
      <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-line px-5 py-4">
        <h2 className="font-serif text-[22px] font-semibold">Histórico completo de lances</h2>
        <p className="text-sm text-muted">Licitantes identificados por pseudônimo</p>
      </div>

      {bids.length === 0 ? (
        <p className="px-6 py-8 text-center text-muted">Nenhum lance registrado ainda.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-190 border-collapse text-left text-[15px]">
            <thead>
              <tr className="border-b border-line text-[13px] text-muted">
                <th scope="col" className="px-4 py-3 font-semibold">#</th>
                <th scope="col" className="px-4 py-3 font-semibold">Licitante</th>
                <th scope="col" className="px-4 py-3 text-right font-semibold">Valor</th>
                <th scope="col" className="px-4 py-3 font-semibold">Horário (UTC)</th>
                <th scope="col" className="px-4 py-3 font-semibold">Hash anterior</th>
                <th scope="col" className="px-4 py-3 font-semibold">Hash</th>
                <th scope="col" className="px-4 py-3 font-semibold">Status</th>
              </tr>
            </thead>
            <tbody>
              {bids.map((bid) => (
                <tr key={bid.sequence} className={`border-b border-line last:border-b-0 ${bid.ok ? "" : "bg-red-soft"}`}>
                  <td className="px-4 py-3 font-mono text-muted">{bid.sequence}</td>
                  <td className="px-4 py-3">{bid.bidder_alias}</td>
                  <td className={`px-4 py-3 text-right font-mono whitespace-nowrap ${bid.ok ? "" : "text-red"}`}>
                    {formatCents(bid.amount)}
                  </td>
                  <td className="px-4 py-3 font-mono text-sm whitespace-nowrap">{formatUtc(bid.created_at)}</td>
                  <td className="px-4 py-3 font-mono text-sm whitespace-nowrap text-muted" title={bid.prev_hash}>
                    {abbreviateHash(bid.prev_hash)}
                  </td>
                  <td className="px-4 py-3 font-mono text-sm whitespace-nowrap" title={bid.hash}>
                    {abbreviateHash(bid.hash)}
                  </td>
                  <td className={`px-4 py-3 text-sm font-semibold whitespace-nowrap ${bid.ok ? "text-green" : "text-red"}`}>
                    {bid.ok ? "OK" : "Com problema"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
