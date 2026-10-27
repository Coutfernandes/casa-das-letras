/** Textos e etiquetas sobre lotes usados em mais de uma tela. */

import type { Lot } from "../types/lot";

/** 0 → "sem lances", 1 → "1 lance", 5 → "5 lances" */
export function bidsLabel(count: number): string {
  if (count === 0) return "sem lances";
  return count === 1 ? "1 lance" : `${count} lances`;
}

export type LotStatus = { label: string; text: string; dot: string };

const MUTED = { text: "text-muted", dot: "bg-muted" };

/** A etiqueta colorida da fase do lote, com as classes do texto e da bolinha. */
export function lotStatus(lot: Lot): LotStatus {
  switch (lot.phase) {
    case "LIVE":
      return { label: "Ao vivo", text: "text-live", dot: "bg-live" };
    case "SCHEDULED":
      return { label: "Agendado", text: "text-gold-dark", dot: "bg-gold" };
    case "CLOSED":
      return { label: lot.winner_alias ? "Arrematado" : "Encerrado sem lances", ...MUTED };
    case "CANCELLED":
      return { label: "Cancelado", ...MUTED };
    default:
      return { label: lot.bid_count > 0 ? "Encerrado" : "Encerrado sem lances", ...MUTED };
  }
}

/** O valor que importa agora: o preço final, o lance atual ou o lance inicial. */
export function lotPrice(lot: Lot): number {
  return lot.final_price ?? lot.current_price ?? lot.starting_price;
}

type BookInfo = {
  authors: string[];
  first_publish_year: number | null;
  edition_count: number | null;
};

/** "Machado de Assis · 1899 · 120 edições", sem os dados que faltarem. */
export function bookByline(book: BookInfo): string {
  const editions = book.edition_count
    ? `${book.edition_count} ${book.edition_count === 1 ? "edição" : "edições"}`
    : null;
  return [book.authors.join(", ") || "Autor desconhecido", book.first_publish_year, editions]
    .filter(Boolean)
    .join(" · ");
}
