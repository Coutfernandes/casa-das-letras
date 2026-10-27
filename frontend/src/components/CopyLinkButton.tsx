import { useEffect, useRef, useState } from "react";

/** Por quanto tempo o botão mostra "Link copiado" antes de voltar ao normal. */
const NOTICE_MS = 2000;

type CopyState = "idle" | "copying" | "copied" | "failed";

const LABELS: Record<CopyState, string> = {
  idle: "Copiar link",
  copying: "Copiando…",
  copied: "Link copiado",
  failed: "Não foi possível copiar",
};

type CopyLinkButtonProps = {
  /** O endereço completo, com o domínio. */
  url: string;
  className: string;
};

/** Copia um endereço para a área de transferência e avisa no próprio botão por 2 segundos. */
export function CopyLinkButton({ url, className }: CopyLinkButtonProps) {
  const [state, setState] = useState<CopyState>("idle");
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  // Se a tela fechar antes dos 2 segundos, o aviso não tenta voltar depois.
  useEffect(() => () => clearTimeout(timer.current), []);

  async function copy() {
    if (state === "copying") return;

    setState("copying");
    let result: CopyState = "copied";
    try {
      // Só funciona em https ou em localhost; fora disso, cai no "Não foi possível copiar".
      await navigator.clipboard.writeText(url);
    } catch {
      result = "failed";
    }
    setState(result);

    clearTimeout(timer.current);
    timer.current = setTimeout(() => setState("idle"), NOTICE_MS);
  }

  return (
    <button type="button" onClick={copy} disabled={state === "copying"} aria-live="polite"
      className={`${className} disabled:cursor-not-allowed disabled:opacity-60`}>
      {LABELS[state]}
    </button>
  );
}
