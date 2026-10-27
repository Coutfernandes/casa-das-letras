import { useState } from "react";

import type { CatalogBook, Lot } from "../../types/lot";
import { CatalogSearch } from "./CatalogSearch";
import { LotForm } from "./LotForm";

type CreateLotSectionProps = {
  onCreated: () => void;
};

export function CreateLotSection({ onCreated }: CreateLotSectionProps) {
  const [book, setBook] = useState<CatalogBook | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  function select(chosen: CatalogBook) {
    setBook(chosen);
    setNotice(null);
  }

  function handleCreated(lot: Lot) {
    setBook(null);
    setNotice(`Lote publicado: ${lot.title}. Ele já aparece em "Meus lotes" e na vitrine.`);
    onCreated();
  }

  return (
    <section className="flex flex-col gap-4">
      <h2 className="font-serif text-[28px] font-semibold">Criar novo lote</h2>
      <div className="flex flex-wrap items-start gap-6">
        <CatalogSearch selectedKey={book?.work_key ?? null} onSelect={select} />
        <LotForm book={book} notice={notice} onCreated={handleCreated} />
      </div>
    </section>
  );
}
