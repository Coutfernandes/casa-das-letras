import { Link } from "react-router";

import { CopyLinkButton } from "../../components/CopyLinkButton";
import { LotCover } from "../../components/LotCover";
import type { MyWonLot } from "../../types/myBids";
import { formatDateTime } from "../../utils/dates";
import { bookByline } from "../../utils/lots";
import { formatCents } from "../../utils/money";
import { receiptPath, receiptUrl } from "../../utils/receipts";

/** Um cartão da aba "Vencidos", com os atalhos para o comprovante e a auditoria. */
export function WonLotCard({ item }: { item: MyWonLot }) {
  const { lot } = item;
  const url = receiptUrl(item.receipt_token);

  const facts = [
    { label: "Valor do arremate", value: formatCents(item.final_price), mono: true },
    { label: "Encerrado em", value: formatDateTime(item.closed_at), mono: false },
    { label: "Lances no lote", value: item.bid_count, mono: true },
  ];

  return (
    <li className="flex flex-wrap gap-6 rounded-md border border-line bg-surface p-5">
      <LotCover title={lot.title} authors={lot.authors} coverUrl={lot.cover_url} />

      <div className="flex min-w-0 flex-[1_1_320px] flex-col gap-4">
        <span className="self-start rounded-full border border-green bg-green-soft px-3 py-1 text-[13px] font-semibold text-green">
          Arrematado por você
        </span>

        <div>
          <h2 className="font-serif text-[26px] leading-tight font-semibold">{lot.title}</h2>
          <p className="text-muted">{bookByline(lot)}</p>
        </div>

        <dl className="grid grid-cols-[repeat(auto-fit,minmax(150px,1fr))] gap-4">
          {facts.map((fact) => (
            <div key={fact.label} className="flex flex-col gap-0.5">
              <dt className="text-[13px] text-muted">{fact.label}</dt>
              <dd className={fact.mono ? "font-mono" : undefined}>{fact.value}</dd>
            </div>
          ))}
        </dl>

        <div className="flex flex-wrap items-center gap-3">
          <Link to={receiptPath(item.receipt_token)}
            className="flex h-11 items-center rounded-md bg-gold-dark px-5 text-[15px] font-semibold text-paper hover:opacity-90">
            Ver comprovante
          </Link>
          <CopyLinkButton url={url}
            className="h-11 rounded-md border border-line px-4 text-[15px] font-semibold hover:bg-paper" />
          <Link to={`/auditoria/${lot.id}`} className="px-1 text-[15px] font-semibold text-gold-dark hover:text-ink">
            Auditar lote
          </Link>
        </div>

        <p className="font-mono text-[13px] break-all text-muted">{url}</p>
      </div>
    </li>
  );
}
