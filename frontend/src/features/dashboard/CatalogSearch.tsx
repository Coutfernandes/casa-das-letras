import { useEffect, useState, type FormEvent } from "react";

import { LotCover } from "../../components/LotCover";
import { ApiError } from "../../services/api";
import { searchCatalog } from "../../services/catalog";
import type { CatalogBook, CatalogSearchResponse } from "../../types/lot";
import { bookByline } from "../../utils/lots";

type Search = { q: string };

type Outcome =
  | { search: Search; kind: "ok"; response: CatalogSearchResponse }
  | { search: Search; kind: "unavailable" }
  | { search: Search; kind: "error" };

const NOTICE = "rounded-md px-4 py-3.5 text-[15px] leading-normal";

type CatalogSearchProps = {
  selectedKey: string | null;
  onSelect: (book: CatalogBook) => void;
};

export function CatalogSearch({ selectedKey, onSelect }: CatalogSearchProps) {
  const [query, setQuery] = useState("");
  const [search, setSearch] = useState<Search | null>(null);
  const [outcome, setOutcome] = useState<Outcome | null>(null);

  useEffect(() => {
    if (!search) return;
    const controller = new AbortController();
    searchCatalog(search.q, 1, controller.signal)
      .then((response) => {
        if (!controller.signal.aborted) setOutcome({ search, kind: "ok", response });
      })
      .catch((error) => {
        if (controller.signal.aborted) return;
        const unavailable = error instanceof ApiError && error.status === 503;
        setOutcome({ search, kind: unavailable ? "unavailable" : "error" });
      });
    return () => controller.abort();
  }, [search]);

  const isLoading = search !== null && outcome?.search !== search;

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSearch({ q: query.trim() });
  }

  function renderOutcome() {
    if (isLoading) {
      return <p className="text-[15px] text-muted">Buscando na Open Library…</p>;
    }
    if (!outcome) {
      return <p className="text-[15px] text-muted">Busque por título ou autor para escolher o livro do lote.</p>;
    }
    if (outcome.kind === "unavailable") {
      return (
        <div role="alert" className={`${NOTICE} border border-red bg-red-soft`}>
          <strong className="text-red">A busca de livros está indisponível agora.</strong> Lotes já
          criados não são afetados: vitrine, salas, auditoria e comprovantes continuam funcionando.
        </div>
      );
    }
    if (outcome.kind === "error") {
      return (
        <p role="alert" className={`${NOTICE} border border-red bg-red-soft`}>
          Não foi possível buscar agora. Confira a sua conexão e tente de novo.
        </p>
      );
    }

    const { results, is_stale } = outcome.response;
    return (
      <>
        {is_stale && (
          <p role="status" className={`${NOTICE} border border-gold bg-gold-soft`}>
            A Open Library não respondeu agora. Estes resultados são da última busca guardada e podem
            estar desatualizados.
          </p>
        )}
        {results.length === 0 ? (
          <p className="text-[15px] text-muted">Nenhum livro com capa encontrado para “{outcome.search.q}”.</p>
        ) : (
          <ul className="flex max-h-120 flex-col gap-2 overflow-y-auto">
            {results.map((book) => {
              const selected = book.work_key === selectedKey;
              return (
                <li key={book.work_key}
                  className={`flex items-center gap-3.5 rounded-md border p-2.5 ${
                    selected ? "border-gold bg-gold-soft" : "border-line"
                  }`}>
                  <LotCover title={book.title} authors={book.authors} coverUrl={book.cover_url} size="thumb" />
                  <span className="flex min-w-0 flex-1 flex-col gap-0.5">
                    <span className="text-[15px] font-semibold">{book.title}</span>
                    <span className="text-[13px] text-muted">{bookByline(book)}</span>
                  </span>
                  <button type="button" onClick={() => onSelect(book)} aria-pressed={selected}
                    className="h-10 shrink-0 rounded-md border border-line bg-surface px-3.5 text-sm font-semibold">
                    {selected ? "Selecionado" : "Selecionar"}
                  </button>
                </li>
              );
            })}
          </ul>
        )}
        <p className="text-[13px] text-muted">Resultados sem capa são ocultados. Fonte: openlibrary.org/search.json</p>
      </>
    );
  }

  return (
    <div className="flex min-w-0 flex-[1_1_460px] flex-col gap-3.5 rounded-md border border-line bg-surface p-5">
      <StepTitle number={1}>Buscar livro na Open Library</StepTitle>
      <form role="search" onSubmit={submit} className="flex gap-2.5">
        <label htmlFor="catalog-query" className="sr-only">Título ou autor</label>
        <input id="catalog-query" type="search" value={query} onChange={(event) => setQuery(event.target.value)}
          required minLength={2} maxLength={200} placeholder="Ex: machado de assis"
          className="h-11 min-w-0 flex-1 rounded-md border border-line bg-paper px-3.5 text-[15px]" />
        <button type="submit" className="h-11 rounded-md bg-ink px-5 text-[15px] font-semibold text-paper">
          Buscar
        </button>
      </form>
      {renderOutcome()}
    </div>
  );
}

export function StepTitle({ number, children }: { number: number; children: string }) {
  return (
    <div className="flex items-center gap-2.5">
      <span className="flex size-7 items-center justify-center rounded-full bg-ink text-[13px] font-bold text-paper">
        {number}
      </span>
      <h3 className="text-[17px] font-semibold">{children}</h3>
    </div>
  );
}
