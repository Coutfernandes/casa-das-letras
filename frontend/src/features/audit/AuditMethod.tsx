import { useEffect, useState } from "react";

import { fetchPublicKey } from "../../services/audit";

/** "Como verificamos": a explicação da cadeia e a chave pública para conferir por conta própria. */
export function AuditMethod() {
  const [publicKey, setPublicKey] = useState<string | null>(null);
  const [hasFailed, setHasFailed] = useState(false);

  // A chave não muda: busca uma vez quando o quadro aparece.
  useEffect(() => {
    const controller = new AbortController();
    fetchPublicKey(controller.signal)
      .then((data) => {
        if (!controller.signal.aborted) setPublicKey(data.public_key);
      })
      .catch(() => {
        if (!controller.signal.aborted) setHasFailed(true);
      });
    return () => controller.abort();
  }, []);

  return (
    <section className="flex min-w-0 flex-[1_1_380px] flex-col gap-3.5 rounded-md border border-line bg-surface p-5">
      <h2 className="font-serif text-[22px] font-semibold">Como verificamos</h2>
      <p className="text-[15px] text-muted">
        Cada lance guarda o hash SHA-256 do lance anterior. Alterar, apagar ou inserir um lance quebra a cadeia a
        partir dali.
      </p>
      <p className="text-[15px] text-muted">
        O lote guarda uma âncora (número de lances e último hash) assinada com Ed25519. Ela detecta a remoção dos
        últimos lances, e sem a chave privada ninguém consegue forjá-la.
      </p>
      <p className="text-[15px] text-muted">
        Cada âncora também é copiada para fora do banco. Assim, restaurar um estado antigo inteiro do histórico
        também é detectado.
      </p>

      <div className="mt-1 flex flex-col gap-1.5 rounded-md border border-line bg-paper px-4 py-3.5">
        <p className="text-[13px] text-muted">Chave pública de verificação</p>
        <p className={`font-mono text-sm break-all ${publicKey ? "" : "text-muted"}`}>
          {publicKey ?? (hasFailed ? "Não foi possível carregar a chave agora." : "Carregando…")}
        </p>
      </div>
    </section>
  );
}
