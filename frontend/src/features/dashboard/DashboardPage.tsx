import { useEffect, useState } from "react";

import { fetchDashboard } from "../../services/lots";
import type { DashboardResponse } from "../../types/lot";
import { formatCents } from "../../utils/money";
import { CreateLotSection } from "./CreateLotSection";
import { MyLotsTable } from "./MyLotsTable";

type Loaded = { version: number; data: DashboardResponse };

const CARD = "rounded-md border px-5 py-4.5";

export function DashboardPage() {
  const [version, setVersion] = useState(0);
  const [loaded, setLoaded] = useState<Loaded | null>(null);
  const [failedVersion, setFailedVersion] = useState<number | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    fetchDashboard(controller.signal)
      .then((data) => {
        if (!controller.signal.aborted) setLoaded({ version, data });
      })
      .catch(() => {
        if (!controller.signal.aborted) setFailedVersion(version);
      });
    return () => controller.abort();
  }, [version]);

  function reload() {
    setVersion((current) => current + 1);
  }

  const hasFailed = failedVersion === version;
  const summary = loaded?.data.summary;

  const cards = [
    { label: "Ao vivo", value: summary?.live },
    { label: "Agendados", value: summary?.scheduled },
    { label: "Encerrados", value: summary?.finished },
  ];

  return (
    <div className="flex flex-col gap-8">
      <div>
        <p className="mb-2 text-[13px] tracking-[0.12em] text-muted uppercase">Leiloeiro</p>
        <h1 className="font-serif text-[44px] leading-tight font-bold">Painel do leiloeiro</h1>
      </div>

      {hasFailed && (
        <div role="alert" className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-red bg-red-soft px-4 py-3">
          <p>Não foi possível carregar o painel. Confira a sua conexão e tente de novo.</p>
          <button type="button" onClick={reload}
            className="h-10 rounded-md border border-line bg-surface px-4 font-semibold">
            Tentar de novo
          </button>
        </div>
      )}

      <div className="grid grid-cols-[repeat(auto-fit,minmax(200px,1fr))] gap-4">
        {cards.map((card) => (
          <div key={card.label} className={`${CARD} border-line bg-surface`}>
            <div className="text-[13px] text-muted">{card.label}</div>
            <div className="font-mono text-[30px] font-medium">{card.value ?? "–"}</div>
          </div>
        ))}
        <div className={`${CARD} border-gold bg-gold-soft`}>
          <div className="text-[13px] text-muted">Total recebido</div>
          <div className="font-mono text-[30px] font-medium">
            {summary ? formatCents(summary.total_received) : "–"}
          </div>
        </div>
      </div>

            <CreateLotSection onCreated={reload} />

      <section className="flex flex-col gap-4">
        <h2 className="font-serif text-[28px] font-semibold">Meus lotes</h2>
        {loaded ? (
          <MyLotsTable lots={loaded.data.results} onChanged={reload} />
        ) : (
          !hasFailed && (
            <p className="rounded-md border border-line bg-surface px-6 py-10 text-center text-muted">
              Carregando seus lotes…
            </p>
          )
        )}
      </section>
    </div>
  );
}
