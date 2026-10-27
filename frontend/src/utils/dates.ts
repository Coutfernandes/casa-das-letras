/** Datas e prazos como a pessoa lê, no fuso horário do navegador dela. */

const DAY_MONTH = new Intl.DateTimeFormat("pt-BR", { day: "2-digit", month: "2-digit" });
const HOUR_MINUTE = new Intl.DateTimeFormat("pt-BR", { hour: "2-digit", minute: "2-digit" });

const SECOND = 1000;
const MINUTE = 60 * SECOND;
const HOUR = 60 * MINUTE;
const DAY = 24 * HOUR;

/** "2026-10-27T18:00:00Z" → "27/10 às 14:00" (em Manaus) */
export function formatDayTime(iso: string): string {
  const date = new Date(iso);
  return `${DAY_MONTH.format(date)} às ${HOUR_MINUTE.format(date)}`;
}

const FULL_DATE = new Intl.DateTimeFormat("pt-BR", { day: "2-digit", month: "2-digit", year: "numeric" });

/** "2026-10-24T01:04:00Z" → "23/10/2026 às 21:04" (em Manaus) */
export function formatDateTime(iso: string): string {
  const date = new Date(iso);
  return `${FULL_DATE.format(date)} às ${HOUR_MINUTE.format(date)}`;
}

/** Milissegundos que faltam → "02:14:37", ou "3 dias" quando falta mais de um dia. */
export function formatRemaining(milliseconds: number): string {
  const remaining = Math.max(0, milliseconds);
  const days = Math.floor(remaining / DAY);
  if (days >= 1) {
    return days === 1 ? "1 dia" : `${days} dias`;
  }

  const hours = Math.floor(remaining / HOUR);
  const minutes = Math.floor((remaining % HOUR) / MINUTE);
  const seconds = Math.floor((remaining % MINUTE) / SECOND);
  return [hours, minutes, seconds].map((part) => String(part).padStart(2, "0")).join(":");
}

/** Date → "2026-10-27T14:00", o formato do <input type="datetime-local">, no fuso do navegador. */
export function toDateTimeInput(date: Date): string {
  const local = new Date(date.getTime() - date.getTimezoneOffset() * MINUTE);
  return local.toISOString().slice(0, 16);
}

/** "2026-10-27T14:00" (no horário local) → Date. Devolve null se o campo estiver vazio ou inválido. */
export function fromDateTimeInput(value: string): Date | null {
  if (!value) return null;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
}

const CLOCK = new Intl.DateTimeFormat("pt-BR", { hour: "2-digit", minute: "2-digit", second: "2-digit" });

/** "2026-10-27T18:03:27Z" → "14:03:27" (em Manaus) */
export function formatClock(iso: string): string {
  return CLOCK.format(new Date(iso));
}
