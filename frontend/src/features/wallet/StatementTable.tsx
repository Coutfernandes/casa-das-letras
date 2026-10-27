import type { WalletEntry, WalletEntryKind } from "../../types/wallet";
import { formatDayTime } from "../../utils/dates";
import { formatCents } from "../../utils/money";

const KIND_LABEL: Record<WalletEntryKind, string> = {
  DEPOSIT: "Depósito simulado",
  SETTLEMENT_DEBIT: "Arremate",
  SETTLEMENT_CREDIT: "Venda",
};

export function StatementTable({ entries }: { entries: WalletEntry[] }) {
  if (entries.length === 0) {
    return (
      <p className="rounded-md border border-line bg-surface px-6 py-10 text-center text-muted">
        Nenhuma movimentação ainda. Faça um depósito para começar.
      </p>
    );
  }

  return (
    <div className="overflow-x-auto rounded-md border border-line bg-surface">
      <table className="w-full min-w-140 border-collapse text-left text-[15px]">
        <thead>
          <tr className="border-b border-line text-[13px] text-muted">
            <th scope="col" className="px-4 py-3 font-semibold">Data</th>
            <th scope="col" className="px-4 py-3 font-semibold">Movimento</th>
            <th scope="col" className="px-4 py-3 font-semibold">Lote</th>
            <th scope="col" className="px-4 py-3 text-right font-semibold">Valor</th>
          </tr>
        </thead>
        <tbody>
          {entries.map((entry) => (
            <tr key={entry.id} className="border-b border-line last:border-b-0">
              <td className="px-4 py-3 text-sm whitespace-nowrap">{formatDayTime(entry.created_at)}</td>
              <td className="px-4 py-3">{KIND_LABEL[entry.kind]}</td>
              <td className="px-4 py-3 text-muted">{entry.lot_title ?? "—"}</td>
              <td className={`px-4 py-3 text-right font-mono whitespace-nowrap ${entry.amount < 0 ? "text-red" : "text-green"}`}>
                {entry.amount > 0 ? "+" : ""}
                {formatCents(entry.amount)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
