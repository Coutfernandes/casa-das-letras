import { Link } from "react-router";

import type { Lot } from "../../types/lot";
import { lotPrice } from "../../utils/lots";
import { formatCents } from "../../utils/money";

type LotResultProps = {
  /** Um lote já liquidado (fase CLOSED). */
  lot: Lot;
  viewerAlias: string | null;
};

/** O resultado do lote liquidado, no lugar do formulário de lance. */
export function LotResult({ lot, viewerAlias }: LotResultProps) {
  const winner = lot.winner_alias;
  const price = formatCents(lotPrice(lot));

  if (!winner) {
    return (
      <p className="rounded-md border border-line bg-surface p-5 text-[15px] font-semibold">
        Lote encerrado sem lances.
      </p>
    );
  }

  if (viewerAlias !== null && winner === viewerAlias) {
    return (
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-green bg-green-soft p-5">
        <p className="flex flex-col gap-0.5">
          <span className="font-serif text-[22px] font-semibold text-green">Você arrematou este lote!</span>
          <span className="text-[15px]">
            Valor do arremate: <span className="font-mono">{price}</span>
          </span>
        </p>
        <Link to="/meus-arremates?aba=vencidos"
          className="flex h-11 items-center rounded-md bg-gold-dark px-5 text-[15px] font-semibold text-paper hover:opacity-90">
          Ver em Meus arremates
        </Link>
      </div>
    );
  }

  return (
    <p className="rounded-md border border-line bg-surface p-5 text-[15px]">
      <span className="font-semibold">Lote encerrado</span> · Arrematado por{" "}
      <span className="font-semibold">{winner}</span> por <span className="font-mono">{price}</span>
    </p>
  );
}
