import { useEffect, useState } from "react";

/** O horário atual em milissegundos, atualizado a cada intervalo (1 segundo por padrão). */
export function useNow(intervalMs = 1000): number {
  const [now, setNow] = useState(Date.now);

  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), intervalMs);
    return () => clearInterval(timer);
  }, [intervalMs]);

  return now;
}
