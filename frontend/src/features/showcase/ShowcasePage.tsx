import { useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router";

import { useAuth } from "../../hooks/useAuth";
import { fetchShowcase } from "../../services/lots";
import type { ShowcaseFilters, ShowcaseResponse, ShowcaseTab } from "../../types/lot";
import { LotCard } from "./LotCard";

const TABS: { id: ShowcaseTab; label: string; empty: string }[] = [
  { id: "live", label: "Ao vivo", empty: "Nenhum lote ao vivo agora." },
  { id: "scheduled", label: "Agendados", empty: "Nenhum lote agendado." },
  { id: "finished", label: "Encerrados", empty: "Nenhum lote encerrado ainda." },
];

type PriceRange = { id: string; label: string; min?: number; max?: number };

/** As faixas do protótipo, em centavos. */
const PRICE_RANGES: PriceRange[] = [
  { id: "any", label: "Qualquer valor" },
  { id: "up-to-1000", label: "Até R$ 1.000", max: 100_000 },
  { id: "1000-to-2000", label: "R$ 1.000 a R$ 2.000", min: 100_000, max: 200_000 },
  { id: "over-2000", label: "Acima de R$ 2.000", min: 200_000 },
];

const FIELD = "h-11 rounded-md border border-line bg-paper px-3.5 text-[15px] font-normal text-ink";

type Shown = { filters: ShowcaseFilters; response: ShowcaseResponse };

export function ShowcasePage() {
  const { user } = useAuth();
  const [filters, setFilters] = useState<ShowcaseFilters>({ phase: "live" });
  const [query, setQuery] = useState("");
  const [rangeId, setRangeId] = useState(PRICE_RANGES[0].id);
  const [shown, setShown] = useState<Shown | null>(null);
  const [failedFilters, setFailedFilters] = useState<ShowcaseFilters | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    fetchShowcase(filters, controller.signal)
      .then((response) => {
        if (!controller.signal.aborted) setShown({ filters, response });
      })
      .catch(() => {
        if (!controller.signal.aborted) setFailedFilters(filters);
      });
    return () => controller.abort();
  }, [filters]);

  const hasFailed = failedFilters === filters;
  const isLoading = !hasFailed && shown?.filters !== filters;
  const activeTab = TABS.find((tab) => tab.id === filters.phase) ?? TABS[0];
  const hasFilters = Boolean(filters.q) || filters.min_price !== undefined || filters.max_price !== undefined;

  function selectTab(phase: ShowcaseTab) {
    setFilters((current) => ({ ...current, phase }));
  }

  function applySearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const range = PRICE_RANGES.find((item) => item.id === rangeId) ?? PRICE_RANGES[0];
    setFilters((current) => ({
      phase: current.phase,
      q: query.trim() || undefined,
      min_price: range.min,
      max_price: range.max,
    }));
  }

  function retry() {
    setFilters((current) => ({ ...current }));
  }

  function renderResults() {
    if (hasFailed) {
      return (
        <div role="alert" className="flex flex-col items-center gap-4 rounded-md border border-line bg-red-soft px-6 py-10 text-center">
          <p>Não foi possível carregar os lotes. Confira a sua conexão e tente de novo.</p>
          <button type="button" onClick={retry} className="h-11 rounded-md border border-line bg-surface px-5 font-semibold">
            Tentar de novo
          </button>
        </div>
      );
    }
    if (!shown || shown.filters.phase !== filters.phase) {
      return <p className="rounded-md border border-line bg-surface px-6 py-10 text-center text-muted">Carregando lotes…</p>;
    }
    if (shown.response.results.length === 0) {
      return (
        <p className="rounded-md border border-line bg-surface px-6 py-10 text-center text-muted">
          {hasFilters ? "Nenhum lote encontrado com esses filtros." : activeTab.empty}
        </p>
      );
    }
    return (
      <div className={`grid grid-cols-[repeat(auto-fill,minmax(260px,1fr))] gap-6 transition-opacity ${isLoading ? "opacity-60" : ""}`}>
        {shown.response.results.map((lot) => (
          <LotCard key={lot.id} lot={lot} isVisitor={!user} />
        ))}
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-8">
      <section className="max-w-170">
        <p className="mb-2.5 text-[13px] tracking-[0.12em] text-muted uppercase">Vitrine</p>
        <h1 className="font-serif text-5xl leading-[1.08] font-bold">Obras raras em disputa agora</h1>
        <p className="mt-3.5 text-[17px] leading-relaxed text-muted">
          Livros catalogados pela Open Library. Cada lance entra numa cadeia de hashes que qualquer
          pessoa pode auditar, mesmo sem login.
        </p>
      </section>

      <form role="search" onSubmit={applySearch}
        className="flex flex-wrap items-end gap-3 rounded-md border border-line bg-surface p-5">
        <label className="flex flex-[1_1_320px] flex-col gap-1.5 text-[13px] font-semibold">
          Título ou autor
          <input type="search" value={query} onChange={(event) => setQuery(event.target.value)}
            placeholder="Ex: Machado de Assis" maxLength={200} className={FIELD} />
        </label>
        <label className="flex flex-[0_1_220px] flex-col gap-1.5 text-[13px] font-semibold">
          Lance atual
          <select value={rangeId} onChange={(event) => setRangeId(event.target.value)} className={FIELD}>
            {PRICE_RANGES.map((range) => (
              <option key={range.id} value={range.id}>{range.label}</option>
            ))}
          </select>
        </label>
        <button type="submit" className="h-11 rounded-md bg-gold-dark px-6 text-[15px] font-semibold text-paper hover:opacity-90">
          Buscar
        </button>
      </form>

      <div role="tablist" aria-label="Estado dos lotes" className="flex flex-wrap gap-x-7 gap-y-1 border-b border-line">
        {TABS.map((tab) => {
          const selected = tab.id === filters.phase;
          return (
            <button key={tab.id} type="button" role="tab" aria-selected={selected} onClick={() => selectTab(tab.id)}
              className={`-mb-px flex h-12 items-center gap-2 border-b-2 text-base font-semibold ${
                selected ? "border-gold text-ink" : "border-transparent text-muted hover:text-ink"
              }`}>
              {tab.label}
              <span className="rounded-full border border-line bg-surface px-2 py-0.5 font-mono text-[13px] font-normal">
                {shown?.response.counts[tab.id] ?? "–"}
              </span>
            </button>
          );
        })}
      </div>

      <section aria-busy={isLoading} aria-label={activeTab.label}>
        {renderResults()}
      </section>

      <section className="flex flex-wrap items-center justify-between gap-4 rounded-md border border-line bg-surface px-6 py-5">
        <div className="flex items-center gap-3.5">
          <svg aria-hidden="true" width="28" height="28" viewBox="0 0 24 24" fill="none"
            stroke="var(--green)" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 3l7 3v5c0 4.5-3 8.3-7 10-4-1.7-7-5.5-7-10V6z" />
            <path d="M9 12l2 2 4-4" />
          </svg>
          <p className="max-w-160 text-[15px] leading-normal">
            Todo histórico de lances é público e verificável. Licitantes aparecem por pseudônimo,
            nunca por nome ou e-mail.
          </p>
        </div>
        <Link to="/auditoria/como-funciona" className="text-[15px] font-semibold text-gold-dark hover:text-ink">
          Como funciona a auditoria
        </Link>
      </section>
    </div>
  );
}
