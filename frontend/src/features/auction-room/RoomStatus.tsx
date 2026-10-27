import type { Lot } from "../../types/lot";
import { formatDayTime } from "../../utils/dates";
import { lotPrice } from "../../utils/lots";
import { formatCents } from "../../utils/money";

type Tone = "good" | "bad" | "neutral";

const TONES: Record<Tone, string> = {
  good: "border-green bg-green-soft text-green",
  bad: "border-red bg-red-soft text-red",
  neutral: "border-line bg-surface text-ink",
};

type RoomStatusProps = {
  /** O lote já com a fase de agora (agendado vira ao vivo, ao vivo vira encerrado). */
  lot: Lot;
  viewerAlias: string | null;
  outbid: boolean;
  cancelReason: string | null;
};

function statusOf({ lot, viewerAlias, outbid, cancelReason }: RoomStatusProps): { tone: Tone; text: string } | null {
  const isMe = (alias: string | null) => viewerAlias !== null && alias === viewerAlias;

  switch (lot.phase) {
    case "CANCELLED":
      return { tone: "bad", text: cancelReason ?? "Lote cancelado pelo leiloeiro." };
    case "SCHEDULED":
      return { tone: "neutral", text: `Lote agendado. Os lances abrem em ${formatDayTime(lot.starts_at)}.` };
    case "LIVE":
      if (isMe(lot.leader_alias)) {
        return { tone: "good", text: `Você está ganhando. Seu lance de ${formatCents(lotPrice(lot))} lidera.` };
      }
      if (outbid) {
        return { tone: "bad", text: "Você foi superado. O valor do seu lance voltou ao disponível." };
      }
      return null;
    default: {
      // Encerrado: enquanto o fechamento não roda, o vencedor ainda é o líder.
      const winner = lot.winner_alias ?? lot.leader_alias;
      const price = formatCents(lotPrice(lot));
      if (!winner) return { tone: "neutral", text: "Lote encerrado sem lances." };
      if (isMe(winner)) return { tone: "good", text: `Lote encerrado. Você arrematou por ${price}.` };
      return { tone: "neutral", text: `Lote encerrado. Arrematado por ${winner} por ${price}.` };
    }
  }
}

/** A faixa que diz à pessoa como ela está no lote. Fica sempre na página para o leitor de tela anunciar as mudanças. */
export function RoomStatus(props: RoomStatusProps) {
  const status = statusOf(props);

  return (
    <div role="status" aria-live="polite">
      {status && (
        <p className={`rounded-md border px-4 py-3 text-[15px] font-semibold ${TONES[status.tone]}`}>{status.text}</p>
      )}
    </div>
  );
}
