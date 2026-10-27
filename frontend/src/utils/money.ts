/**
 * A API guarda dinheiro em centavos (inteiros), para nunca errar em contas com vírgula.
 * Aqui ficam as conversões entre os centavos e o que a pessoa vê e digita.
 */

const BRL = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });

/** 125000 → "R$ 1.250,00" */
export function formatCents(cents: number): string {
  return BRL.format(cents / 100);
}

/**
 * O que a pessoa digita → centavos. Aceita "1250", "1.250", "1.250,5" e "R$ 1.250,50".
 * Devolve null quando o texto não é um valor válido.
 */
export function parseReais(text: string): number | null {
  const cleaned = text.replace(/R\$|\s|\./g, "");
  const match = /^(\d{1,9})(?:,(\d{1,2}))?$/.exec(cleaned);
  if (!match) return null;

  const [, reais, centavos = "0"] = match;
  return Number(reais) * 100 + Number(centavos.padEnd(2, "0"));
}

const AMOUNT_INPUT = new Intl.NumberFormat("pt-BR", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

/** 50000 → "500,00": o valor no formato do campo, sem o "R$". */
export function formatAmountInput(cents: number): string {
  return AMOUNT_INPUT.format(cents / 100);
}
