import { useEffect, useState } from "react";
import { Link } from "react-router";

import { Countdown } from "../../components/Countdown";
import { LotCover } from "../../components/LotCover";
import { fetchWallet } from "../../services/wallet";
import type { Wallet } from "../../types/wallet";
import { formatCents } from "../../utils/money";
import { DepositForm } from "./DepositForm";
import { StatementTable } from "./StatementTable";

type Loaded = { version: number; wallet: Wallet };

function committedCaption(count: number): string {
  if (count === 0) return "Nenhum lance liderando agora";
  return count === 1 ? "Você lidera 1 lote" : `Você lidera ${count} lotes`;
}

export function WalletPage() {
  const [version, setVersion] = useState(0);
  const [loaded, setLoaded] = useState<Loaded | null>(null);
  const [failedVersion, setFailedVersion] = useState<number | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    fetchWallet(controller.signal)
      .then((wallet) => {
        if (!controller.signal.aborted) setLoaded({ version, wallet });
      })
      .catch(() => {
        if (!controller.signal.aborted) setFailedVersion(version);
      });
    return () => controller.abort();
  }, [version]);

  const wallet = loaded?.wallet;
  const hasFailed = failedVersion === version;

  function showDeposit(updated: Wallet) {
    setLoaded({ version, wallet: updated });
  }

  const cards = [
    { label: "Saldo total", value: wallet?.total, caption: "Soma de depósitos e arremates", highlight: false },
    { label: "Comprometido", value: wallet?.committed, caption: committedCaption(wallet?.committed_lots.length ?? 0), highlight: false },
    { label: "Disponível para lances", value: wallet?.available, caption: "Total menos comprometido", highlight: true },
  ];

  return (
    <div className="flex flex-col gap-8">
      <div>
        <p className="mb-2 text-[13px] tracking-[0.12em] text-muted uppercase">Licitante</p>
        <h1 className="font-serif text-[44px] leading-tight font-bold">Carteira</h1>
      </div>

      {hasFailed && (
        <div role="alert" className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-red bg-red-soft px-4 py-3">
          <p>Não foi possível carregar a carteira. Confira a sua conexão e tente de novo.</p>
          <button type="button" onClick={() => setVersion((current) => current + 1)}
            className="h-10 rounded-md border border-line bg-surface px-4 font-semibold">
            Tentar de novo
          </button>
        </div>
      )}

      <div className="grid grid-cols-[repeat(auto-fit,minmax(240px,1fr))] gap-4">
        {cards.map((card) => (
          <div key={card.label}
            className={`flex flex-col gap-1 rounded-md border px-5 py-4.5 ${card.highlight ? "border-gold bg-gold-soft" : "border-line bg-surface"}`}>
            <span className="text-[13px] text-muted">{card.label}</span>
            <span className="font-mono text-[30px] font-medium">{card.value === undefined ? "–" : formatCents(card.value)}</span>
            <span className="text-[13px] text-muted">{wallet ? card.caption : ""}</span>
          </div>
        ))}
      </div>

      <div className="flex flex-wrap items-start gap-6">
        <DepositForm onDeposited={showDeposit} />

        <section className="flex min-w-0 flex-[1_1_380px] flex-col gap-3.5 rounded-md border border-line bg-surface p-5">
          <h2 className="font-serif text-[22px] font-semibold">Por que está comprometido</h2>
          <p className="text-sm text-muted">
            Enquanto você lidera um lote, o valor do lance fica reservado. Se alguém cobrir, ele volta ao
            disponível na hora.
          </p>

          {wallet && wallet.committed_lots.length === 0 && (
            <p className="rounded-md bg-paper px-3.5 py-3 text-sm text-muted">Você não lidera nenhum lote agora.</p>
          )}

          {wallet?.committed_lots.map((lot) => (
            <Link key={lot.id} to={`/lotes/${lot.id}`}
              className="flex items-center gap-3.5 rounded-md border border-line p-2.5 hover:bg-paper">
              <LotCover title={lot.title} authors={lot.authors} coverUrl={lot.cover_url} size="thumb" />
              <span className="flex min-w-0 flex-1 flex-col gap-0.5">
                <span className="font-semibold">{lot.title}</span>
                <span className="text-[13px] text-green">
                  {lot.phase === "LIVE" ? (
                    <>Você está ganhando · termina em <Countdown endsAt={lot.ends_at} /></>
                  ) : (
                    "Encerrado, aguardando liquidação"
                  )}
                </span>
              </span>
              <span className="font-mono whitespace-nowrap">{formatCents(lot.current_price ?? 0)}</span>
            </Link>
          ))}

          {wallet && (
            <dl className="mt-1 flex flex-col gap-1.5 border-t border-line pt-3.5 font-mono text-sm">
              <div className="flex justify-between"><dt>Saldo total</dt><dd>{formatCents(wallet.total)}</dd></div>
              <div className="flex justify-between"><dt>− Comprometido</dt><dd>{formatCents(wallet.committed)}</dd></div>
              <div className="flex justify-between font-semibold"><dt>= Disponível</dt><dd>{formatCents(wallet.available)}</dd></div>
            </dl>
          )}
        </section>
      </div>

      <section className="flex flex-col gap-4">
        <h2 className="font-serif text-[28px] font-semibold">Extrato</h2>
        {wallet ? (
          <StatementTable entries={wallet.entries} />
        ) : (
          !hasFailed && <p className="rounded-md border border-line bg-surface px-6 py-10 text-center text-muted">Carregando a carteira…</p>
        )}
      </section>
    </div>
  );
}
