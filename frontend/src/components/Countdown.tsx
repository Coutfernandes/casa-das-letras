import { useNow } from "../hooks/useNow";
import { formatRemaining } from "../utils/dates";

const DAY_MS = 24 * 60 * 60 * 1000;

/** O tempo que falta até um horário, atualizado a cada segundo. */
export function Countdown({ endsAt }: { endsAt: string }) {
  const now = useNow();
  const remaining = Date.parse(endsAt) - now;

  return (
    <time dateTime={endsAt} className={remaining < DAY_MS ? "font-mono" : undefined}>
      {remaining > 0 ? formatRemaining(remaining) : "encerrando…"}
    </time>
  );
}
