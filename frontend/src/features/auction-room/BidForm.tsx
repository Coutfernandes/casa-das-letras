import { useState, type FormEvent } from "react";

import { ApiError } from "../../services/api";
import { placeBid } from "../../services/bids";
import { apiErrorMessage } from "../../services/errors";
import type { PlacedBid } from "../../types/bid";
import type { Lot } from "../../types/lot";
import { formatDayTime } from "../../utils/dates";
import { formatAmountInput, formatCents, parseReais } from "../../utils/money";

/** 422 traz o "message" da regra de negócio; 400 traz { amount: [msg] }. */
function bidError(error: unknown): string {
  if (error instanceof ApiError && error.status === 400 && typeof error.data === "object" && error.data) {
    const messages = (error.data as { amount?: unknown }).amount;
    if (Array.isArray(messages) && typeof messages[0] === "string") return messages[0];
  }
  return apiErrorMessage(error, "Não foi possível enviar o lance. Confira a sua conexão e tente de novo.");
}

type BidFormProps = {
  lot: Lot;
  /** Verdadeiro só enquanto o lote está ao vivo; agendado mostra o formulário desligado. */
  isOpen: boolean;
  /** O disponível da carteira, ou null enquanto carrega. */
  available: number | null;
  onPlaced: (placed: PlacedBid) => void;
};

export function BidForm({ lot, isOpen, available, onPlaced }: BidFormProps) {
  const [amount, setAmount] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const minimum = lot.minimum_next_bid;
  const disabled = !isOpen || submitting;

  function fillMinimum() {
    setAmount(formatAmountInput(minimum));
    setError(null);
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (submitting || !isOpen) return;

    const cents = parseReais(amount);
    if (!cents) {
      setError("Informe o valor do lance em reais, como 1.250,00.");
      return;
    }
    if (cents < minimum) {
      setError(`O lance mínimo agora é ${formatCents(minimum)}.`);
      return;
    }

    setSubmitting(true);
    setError(null);
    setNotice(null);
    try {
      const placed = await placeBid(lot.id, cents);
      setAmount("");
      setNotice(`Lance de ${formatCents(placed.bid.amount)} aceito.`);
      onPlaced(placed);
    } catch (caught) {
      setError(bidError(caught));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={submit} noValidate className="flex flex-col gap-3 rounded-md border border-line bg-surface p-5">
      <label htmlFor="bid-amount" className="text-[13px] font-semibold">Seu lance</label>
      <div className="flex flex-wrap gap-2.5">
        <div className={`flex h-12 min-w-0 flex-[1_1_200px] items-center rounded-md border bg-paper px-3.5 ${error ? "border-red" : "border-line"} ${isOpen ? "" : "opacity-60"}`}>
          <span aria-hidden="true" className="mr-2 font-mono text-muted">R$</span>
          <input id="bid-amount" inputMode="decimal" value={amount} placeholder={formatAmountInput(minimum)}
            disabled={!isOpen}
            onChange={(event) => setAmount(event.target.value)}
            aria-invalid={Boolean(error)} aria-describedby={error ? "bid-error bid-hint" : "bid-hint"}
            className="h-full min-w-0 flex-1 bg-transparent font-mono text-lg outline-none disabled:cursor-not-allowed" />
        </div>
        <button type="button" onClick={fillMinimum} disabled={!isOpen}
          className="h-12 rounded-md border border-line px-4 text-sm font-semibold hover:bg-paper disabled:cursor-not-allowed disabled:opacity-60">
          Usar mínimo
        </button>
        <button type="submit" disabled={disabled}
          className="h-12 flex-[1_1_140px] rounded-md bg-gold-dark px-5 text-base font-semibold text-paper disabled:cursor-not-allowed disabled:opacity-60">
          {submitting ? "Enviando…" : "Dar lance"}
        </button>
      </div>

      <p id="bid-hint" className="text-[13px] text-muted">
        {isOpen ? (
          <>
            Mínimo agora <span className="font-mono text-ink">{formatCents(minimum)}</span>
            {" · "}
            Disponível <span className="font-mono text-ink">{available === null ? "–" : formatCents(available)}</span>
          </>
        ) : (
          `Abre em ${formatDayTime(lot.starts_at)}`
        )}
      </p>

      {error && <p id="bid-error" role="alert" className="text-sm text-red">{error}</p>}
      {notice && (
        <p role="status" className="rounded-md border border-green bg-green-soft px-3.5 py-2.5 text-sm font-semibold text-green">
          {notice}
        </p>
      )}
    </form>
  );
}
