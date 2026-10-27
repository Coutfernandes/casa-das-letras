/** O comprovante público de arremate como a API devolve. Valores em centavos. */

export interface Receipt {
  token: string;
  lot_id: string;
  title: string;
  authors: string[];
  first_publish_year: number | null;
  /** Só o pseudônimo: o comprovante nunca mostra nome nem e-mail. */
  winner_alias: string;
  amount: number;
  closed_at: string;
  bid_count: number;
  auctioneer_name: string;
  issued_at: string;
  last_bid_hash: string;
}
