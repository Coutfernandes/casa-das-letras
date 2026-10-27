import { useState, type FormEvent } from "react";

import { ApiError } from "../../services/api";
import { apiErrorMessage } from "../../services/errors";
import { depositMoney } from "../../services/wallet";
import type { Wallet } from "../../types/wallet";
import { formatAmountInput, formatCents, parseReais } from "../../utils/money";

/** O mesmo limite do backend: R$ 100.000,00 por depósito. */
const MAX_DEPOSIT = 100_000_00;
const QUICK_AMOUNTS = [10_000, 50_000, 100_000];

function depositError(error: unknown): string {
  if (error instanceof ApiError && error.status === 400 && typeof error.data === "object" && error.data) {
    const messages = (error.data as { amount?: unknown }).amount;
    if (Array.isArray(messages) && typeof messages[0] === "string") return messages[0];
  }
  return apiErrorMessage(error, "Não foi possível depositar agora. Confira a sua conexão e tente de novo.");
}

export function DepositForm({ onDeposited }: { onDeposited: (wallet: Wallet) => void }) {
  const [amount, setAmount] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  function addQuick(cents: number) {
    const current = parseReais(amount) ?? 0;
    setAmount(formatAmountInput(Math.min(current + cents, MAX_DEPOSIT)));
    setError(null);
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (submitting) return;

    const cents = parseReais(amount);
    if (!cents || cents > MAX_DEPOSIT) {
      setError("Informe um valor entre R$ 0,01 e R$ 100.000,00.");
      return;
    }

    setSubmitting(true);
    setError(null);
    setNotice(null);
    try {
      const wallet = await depositMoney(cents);
      setAmount("");
      setNotice(`Depósito de ${formatCents(cents)} feito. Disponível agora: ${formatCents(wallet.available)}.`);
      onDeposited(wallet);
    } catch (caught) {
      setError(depositError(caught));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={submit} noValidate
      className="flex min-w-0 flex-[1_1_380px] flex-col gap-3.5 rounded-md border border-line bg-surface p-5">
      <h2 className="font-serif text-[22px] font-semibold">Depositar saldo</h2>
      <p className="text-sm text-muted">Depósito simulado, sem dinheiro real. Até R$ 100.000,00 por vez.</p>

      <label htmlFor="deposit-amount" className="text-[13px] font-semibold">Valor</label>
      <div className={`flex h-12 items-center rounded-md border bg-paper px-3.5 ${error ? "border-red" : "border-line"}`}>
        <span aria-hidden="true" className="mr-2 font-mono text-muted">R$</span>
        <input id="deposit-amount" inputMode="decimal" value={amount} placeholder="0,00"
          onChange={(event) => setAmount(event.target.value)}
          aria-invalid={Boolean(error)} aria-describedby={error ? "deposit-error" : undefined}
          className="h-full min-w-0 flex-1 bg-transparent font-mono text-lg outline-none" />
      </div>

      <div className="flex flex-wrap gap-2">
        {QUICK_AMOUNTS.map((cents) => (
          <button key={cents} type="button" onClick={() => addQuick(cents)}
            className="h-10 rounded-md border border-line px-3.5 text-sm font-semibold hover:bg-paper">
            + {formatCents(cents).replace(",00", "")}
          </button>
        ))}
      </div>

      {error && <p id="deposit-error" role="alert" className="text-sm text-red">{error}</p>}

      <button type="submit" disabled={submitting}
        className="h-12 rounded-md bg-gold-dark text-base font-semibold text-paper disabled:cursor-not-allowed disabled:opacity-60">
        {submitting ? "Depositando…" : "Depositar"}
      </button>

      {notice && (
        <p role="status" className="rounded-md border border-green bg-green-soft px-3.5 py-3 text-sm font-semibold text-green">
          {notice}
        </p>
      )}
    </form>
  );
}
