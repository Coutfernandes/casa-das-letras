import { LotCover } from "../../components/LotCover";
import type { Lot } from "../../types/lot";
import { formatDayTime } from "../../utils/dates";
import { formatCents } from "../../utils/money";

/** A coluna da esquerda: a capa, os dados do livro e do lote e a nota do leiloeiro. */
export function LotDetails({ lot }: { lot: Lot }) {
  const attributes = [
    { label: lot.authors.length > 1 ? "Autores" : "Autor", value: lot.authors.join(", ") || "Autor desconhecido" },
    { label: "Ano", value: lot.first_publish_year ?? "—" },
    { label: "Edições", value: lot.edition_count ?? "—" },
    { label: "Lance inicial", value: formatCents(lot.starting_price), mono: true },
    { label: "Incremento", value: formatCents(lot.min_increment), mono: true },
    { label: "Início", value: formatDayTime(lot.starts_at) },
    { label: "Fim original", value: formatDayTime(lot.original_ends_at) },
  ];

  return (
    <aside className="flex flex-col gap-6">
      <div className="flex justify-center rounded-md border border-line bg-surface py-8">
        <LotCover title={lot.title} authors={lot.authors} coverUrl={lot.cover_url} />
      </div>

      <dl className="flex flex-col rounded-md border border-line bg-surface px-5 py-2 text-[15px]">
        {attributes.map((attribute) => (
          <div key={attribute.label} className="flex justify-between gap-4 border-b border-line py-2.5 last:border-b-0">
            <dt className="text-muted">{attribute.label}</dt>
            <dd className={`text-right ${attribute.mono ? "font-mono" : ""}`}>{attribute.value}</dd>
          </div>
        ))}
      </dl>

      {lot.description && (
        <section className="flex flex-col gap-2 rounded-md border border-line bg-surface p-5">
          <h2 className="font-serif text-lg font-semibold">Nota do leiloeiro</h2>
          <p className="text-[15px] leading-relaxed whitespace-pre-line">{lot.description}</p>
          <p className="text-[13px] text-muted">— {lot.auctioneer_name}</p>
        </section>
      )}
    </aside>
  );
}
