import { useState } from "react";

import { apiErrorMessage } from "../../services/errors";
import { cancelLot } from "../../services/lots";
import type { Lot } from "../../types/lot";
import { formatDayTime } from "../../utils/dates";
import { lotPrice, lotStatus } from "../../utils/lots";
import { formatCents } from "../../utils/money";

const OPEN_PHASES = ["LIVE", "SCHEDULED"];

function resultOf(lot: Lot): string {
  switch (lot.phase) {
    case "LIVE":
      return "Em andamento";
    case "SCHEDULED":
      return `Abre ${formatDayTime(lot.starts_at)}`;
    case "CLOSED":
      return lot.winner_alias ? `${lot.winner_alias} · ${formatCents(lotPrice(lot))}` : "Sem lances";
    case "CANCELLED":
      return "Cancelado por você";
    case "ENDED":
      return "Aguardando liquidação";
  }
}

type MyLotsTableProps = {
  lots: Lot[];
  onChanged: () => void;
};

export function MyLotsTable({ lots, onChanged }: MyLotsTableProps) {
  const [confirmingId, setConfirmingId] = useState<string | null>(null);
  const [cancellingId, setCancellingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function cancel(lot: Lot) {
    setCancellingId(lot.id);
    setError(null);
    try {
      await cancelLot(lot.id);
      onChanged();
    } catch (caught) {
      const reason = apiErrorMessage(caught, "Não foi possível cancelar o lote. Tente de novo.");
      setError(`${lot.title}: ${reason}`);
    } finally {
      setCancellingId(null);
      setConfirmingId(null);
    }
  }

  function renderAction(lot: Lot) {
    const isOpen = OPEN_PHASES.includes(lot.phase);
    if (!isOpen) {
      return <span className="text-muted">—</span>;
    }
    if (lot.bid_count > 0) {
      return <span className="text-sm text-muted">Tem lances</span>;
    }
    if (cancellingId === lot.id) {
      return <span className="text-sm text-muted">Cancelando…</span>;
    }
    if (confirmingId === lot.id) {
      return (
        <span className="flex items-center gap-2">
          <span className="text-sm">Cancelar?</span>
          <button type="button" onClick={() => cancel(lot)}
            className="h-9 rounded-md bg-red px-3 text-sm font-semibold text-paper">
            Sim
          </button>
          <button type="button" onClick={() => setConfirmingId(null)}
            className="h-9 rounded-md border border-line px-3 text-sm font-semibold">
            Não
          </button>
        </span>
      );
    }
    return (
      <button type="button" onClick={() => setConfirmingId(lot.id)}
        className="h-9 rounded-md border border-line px-3 text-sm font-semibold text-red hover:bg-red-soft">
        Cancelar
      </button>
    );
  }

  if (lots.length === 0) {
    return (
      <p className="rounded-md border border-line bg-surface px-6 py-10 text-center text-muted">
        Você ainda não criou nenhum lote.
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      {error && (
        <p role="alert" className="rounded-md border border-red bg-red-soft px-4 py-3 text-sm">
          {error}
        </p>
      )}
      <div className="overflow-x-auto rounded-md border border-line bg-surface">
        <table className="w-full min-w-180 border-collapse text-left text-[15px]">
          <thead>
            <tr className="border-b border-line text-[13px] text-muted">
              <th scope="col" className="px-4 py-3 font-semibold">Livro</th>
              <th scope="col" className="px-4 py-3 font-semibold">Estado</th>
              <th scope="col" className="px-4 py-3 font-semibold">Lances</th>
              <th scope="col" className="px-4 py-3 font-semibold">Valor</th>
              <th scope="col" className="px-4 py-3 font-semibold">Resultado</th>
              <th scope="col" className="px-4 py-3 font-semibold">Ação</th>
            </tr>
          </thead>
          <tbody>
            {lots.map((lot) => {
              const status = lotStatus(lot);
              return (
                <tr key={lot.id} className="border-b border-line last:border-b-0">
                  <td className="px-4 py-3">
                    <span className="block font-semibold">{lot.title}</span>
                    <span className="text-[13px] text-muted">
                      {lot.authors.join(", ") || "Autor desconhecido"}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center gap-1.5 text-sm font-semibold whitespace-nowrap ${status.text}`}>
                      <span aria-hidden="true" className={`size-2 rounded-full ${status.dot}`} />
                      {status.label}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-mono">{lot.bid_count}</td>
                  <td className="px-4 py-3 font-mono whitespace-nowrap">{formatCents(lotPrice(lot))}</td>
                  <td className="px-4 py-3 text-sm">{resultOf(lot)}</td>
                  <td className="px-4 py-3">{renderAction(lot)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
