import { useEffect, useState, type KeyboardEvent } from "react";
import { Link, useSearchParams } from "react-router";

import { fetchMyBids } from "../../services/myBids";
import type { MyBidsResponse } from "../../types/myBids";
import { OpenBidRow } from "./OpenBidRow";
import { WonLotCard } from "./WonLotCard";

type Tab = "bids" | "won";
type Loaded = { version: number; data: MyBidsResponse };

const TABS: { id: Tab; label: string }[] = [
  { id: "bids", label: "Lotes com lance" },
  { id: "won", label: "Vencidos" },
];

const PANEL_ID = "my-bids-panel";

function tabId(tab: Tab) {
  return `my-bids-tab-${tab}`;
}

function EmptyState({ text }: { text: string }) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-md border border-line bg-surface px-6 py-10 text-center">
      <p className="text-muted">{text}</p>
      <Link to="/" className="font-semibold text-gold-dark hover:text-ink">Ir para a vitrine</Link>
    </div>
  );
}

export function MyBidsPage() {
  const [version, setVersion] = useState(0);
  const [loaded, setLoaded] = useState<Loaded | null>(null);
  const [failedVersion, setFailedVersion] = useState<number | null>(null);

  // A aba fica no endereço (?aba=vencidos): dá para voltar a ela e mandar o link direto.
  const [searchParams, setSearchParams] = useSearchParams();
  const tab: Tab = searchParams.get("aba") === "vencidos" ? "won" : "bids";

  useEffect(() => {
    const controller = new AbortController();
    fetchMyBids(controller.signal)
      .then((data) => {
        if (!controller.signal.aborted) setLoaded({ version, data });
      })
      .catch(() => {
        if (!controller.signal.aborted) setFailedVersion(version);
      });
    return () => controller.abort();
  }, [version]);

  const data = loaded?.data;
  const hasFailed = failedVersion === version;

  function selectTab(next: Tab) {
    setSearchParams(next === "won" ? { aba: "vencidos" } : {}, { replace: true });
  }

  /** As setas trocam de aba, como o leitor de tela espera de uma lista de abas. */
  function handleTabKeys(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
    event.preventDefault();
    const next: Tab = tab === "bids" ? "won" : "bids";
    selectTab(next);
    document.getElementById(tabId(next))?.focus();
  }

  return (
    <div className="flex flex-col gap-8">
      <div>
        <p className="mb-2 text-[13px] tracking-[0.12em] text-muted uppercase">Licitante</p>
        <h1 className="font-serif text-[44px] leading-tight font-bold">Meus arremates</h1>
      </div>

      {hasFailed && (
        <div role="alert" className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-red bg-red-soft px-4 py-3">
          <p>Não foi possível carregar os seus arremates. Confira a sua conexão e tente de novo.</p>
          <button type="button" onClick={() => setVersion((current) => current + 1)}
            className="h-10 rounded-md border border-line bg-surface px-4 font-semibold">
            Tentar de novo
          </button>
        </div>
      )}

      <div className="flex flex-col gap-5">
        <div role="tablist" aria-label="Meus arremates" onKeyDown={handleTabKeys}
          className="flex gap-6 border-b border-line">
          {TABS.map(({ id, label }) => {
            const selected = id === tab;
            return (
              <button key={id} id={tabId(id)} type="button" role="tab"
                aria-selected={selected} aria-controls={selected ? PANEL_ID : undefined}
                tabIndex={selected ? 0 : -1} onClick={() => selectTab(id)}
                className={`-mb-px flex items-center gap-2 border-b-2 py-2.5 text-[15px] ${
                  selected ? "border-gold font-semibold text-ink" : "border-transparent text-muted hover:text-ink"
                }`}>
                {label}
                <span className="rounded-full border border-line bg-paper px-2 font-mono text-[13px] font-normal">
                  {data ? data.counts[id] : "–"}
                </span>
              </button>
            );
          })}
        </div>

        <div id={PANEL_ID} role="tabpanel" aria-labelledby={tabId(tab)}>
          {!data ? (
            !hasFailed && (
              <p className="rounded-md border border-line bg-surface px-6 py-10 text-center text-muted">
                Carregando os seus arremates…
              </p>
            )
          ) : tab === "bids" ? (
            data.bids.length === 0 ? (
              <EmptyState text="Você ainda não deu lances." />
            ) : (
              <ul className="flex flex-col gap-3">
                {data.bids.map((item) => <OpenBidRow key={item.lot.id} item={item} />)}
              </ul>
            )
          ) : data.won.length === 0 ? (
            <EmptyState text="Você ainda não arrematou nenhum lote." />
          ) : (
            <ul className="flex flex-col gap-4">
              {data.won.map((item) => <WonLotCard key={item.lot.id} item={item} />)}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
