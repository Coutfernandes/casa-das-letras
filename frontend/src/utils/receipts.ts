/** Os endereços do comprovante público. */

/** "abc123" → "/comprovante/abc123", para os links dentro da aplicação. */
export function receiptPath(token: string): string {
  return `/comprovante/${token}`;
}

/** O endereço completo, com o domínio, para copiar e mandar a outra pessoa. */
export function receiptUrl(token: string): string {
  return `${window.location.origin}${receiptPath(token)}`;
}
