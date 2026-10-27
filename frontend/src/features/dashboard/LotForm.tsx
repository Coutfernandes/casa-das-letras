import { useState, type FormEvent } from "react";

import { LotCover } from "../../components/LotCover";
import { ApiError } from "../../services/api";
import { apiErrorMessage } from "../../services/errors";
import { createLot } from "../../services/lots";
import type { CatalogBook, Lot, NewLot } from "../../types/lot";
import { fromDateTimeInput, toDateTimeInput } from "../../utils/dates";
import { bookByline } from "../../utils/lots";
import { parseReais } from "../../utils/money";
import { StepTitle } from "./CatalogSearch";

type FieldErrors = Partial<Record<string, string>>;

const DAY_MS = 24 * 60 * 60 * 1000;
const LABEL = "flex flex-col gap-1.5 text-[13px] font-semibold";
const INPUT = "h-11 rounded-md border border-line bg-paper px-3 text-[15px] font-normal text-ink aria-invalid:border-red";

/** Começa agora (no minuto cheio) e termina daqui a um dia. */
function defaultPeriod() {
  const start = new Date();
  start.setSeconds(0, 0);
  return { startsAt: toDateTimeInput(start), endsAt: toDateTimeInput(new Date(start.getTime() + DAY_MS)) };
}

/** Os erros da API viram mensagens por campo (400) ou uma mensagem geral (422 e o resto). */
function errorsFrom(error: unknown): FieldErrors {
  if (error instanceof ApiError && error.status === 400 && typeof error.data === "object" && error.data) {
    const errors: FieldErrors = {};
    for (const [field, messages] of Object.entries(error.data)) {
      errors[field] = Array.isArray(messages) && typeof messages[0] === "string" ? messages[0] : "Valor inválido.";
    }
    return errors;
  }
  return { form: apiErrorMessage(error, "Não foi possível publicar o lote. Confira a sua conexão e tente de novo.") };
}

function FieldError({ id, message }: { id: string; message?: string }) {
  if (!message) return null;
  return <span id={id} className="text-[13px] font-normal text-red">{message}</span>;
}

type LotFormProps = {
  book: CatalogBook | null;
  notice: string | null;
  onCreated: (lot: Lot) => void;
};

export function LotForm({ book, notice, onCreated }: LotFormProps) {
  const [initial] = useState(defaultPeriod);
  const [startingPrice, setStartingPrice] = useState("");
  const [minIncrement, setMinIncrement] = useState("50,00");
  const [startsAt, setStartsAt] = useState(initial.startsAt);
  const [endsAt, setEndsAt] = useState(initial.endsAt);
  const [description, setDescription] = useState("");
  const [errors, setErrors] = useState<FieldErrors>({});
  const [submitting, setSubmitting] = useState(false);

  function validate(): { payload: NewLot | null; errors: FieldErrors } {
    const found: FieldErrors = {};
    const startingCents = parseReais(startingPrice);
    const incrementCents = parseReais(minIncrement);
    const starts = fromDateTimeInput(startsAt);
    const ends = fromDateTimeInput(endsAt);

    if (!startingCents) found.starting_price = "Informe um valor maior que zero, como 600,00.";
    if (!incrementCents) found.min_increment = "Informe um valor maior que zero, como 50,00.";
    if (!starts) found.starts_at = "Informe a data e a hora de início.";
    if (!ends) found.ends_at = "Informe a data e a hora de fim.";
    else if (starts && ends <= starts) found.ends_at = "O fim precisa ser depois do início.";

    if (!book || !startingCents || !incrementCents || !starts || !ends || Object.keys(found).length > 0) {
      return { payload: null, errors: found };
    }
    return {
      errors: found,
      payload: {
        book: {
          work_key: book.work_key,
          title: book.title,
          authors: book.authors,
          first_publish_year: book.first_publish_year,
          edition_count: book.edition_count,
          cover_id: book.cover_id,
        },
        description: description.trim(),
        starting_price: startingCents,
        min_increment: incrementCents,
        starts_at: starts.toISOString(),
        ends_at: ends.toISOString(),
      },
    };
  }

  async function publish(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (submitting) return;

    const { payload, errors: found } = validate();
    setErrors(found);
    if (!payload) return;

    setSubmitting(true);
    try {
      const lot = await createLot(payload);
      setDescription("");
      onCreated(lot);
    } catch (error) {
      setErrors(errorsFrom(error));
    } finally {
      setSubmitting(false);
    }
  }

  const buttonLabel = !book ? "Selecione um livro no passo 1" : submitting ? "Publicando…" : "Publicar lote";

  return (
    <form onSubmit={publish} noValidate
      className="flex min-w-0 flex-[1_1_380px] flex-col gap-3.5 rounded-md border border-line bg-surface p-5">
      <StepTitle number={2}>Definir o lote</StepTitle>

      <div className="flex items-center gap-3.5 rounded-md bg-paper p-3">
        {book ? (
          <>
            <LotCover title={book.title} authors={book.authors} coverUrl={book.cover_url} size="thumb" />
            <span className="flex flex-col gap-0.5">
              <span className="font-serif text-lg font-semibold">{book.title}</span>
              <span className="text-[13px] text-muted">{bookByline(book)}</span>
            </span>
          </>
        ) : (
          <span className="text-[15px] text-muted">Nenhum livro selecionado ainda.</span>
        )}
      </div>

      <div className="grid grid-cols-2 gap-3">
        <label className={LABEL}>
          Lance inicial (R$)
          <input inputMode="decimal" value={startingPrice} onChange={(event) => setStartingPrice(event.target.value)}
            placeholder="600,00" aria-invalid={Boolean(errors.starting_price)} aria-describedby="error-starting-price"
            className={`${INPUT} font-mono`} />
          <FieldError id="error-starting-price" message={errors.starting_price} />
        </label>
        <label className={LABEL}>
          Incremento mínimo (R$)
          <input inputMode="decimal" value={minIncrement} onChange={(event) => setMinIncrement(event.target.value)}
            aria-invalid={Boolean(errors.min_increment)} aria-describedby="error-min-increment"
            className={`${INPUT} font-mono`} />
          <FieldError id="error-min-increment" message={errors.min_increment} />
        </label>
        <label className={LABEL}>
          Início
          <input type="datetime-local" value={startsAt} onChange={(event) => setStartsAt(event.target.value)}
            aria-invalid={Boolean(errors.starts_at)} aria-describedby="error-starts-at" className={INPUT} />
          <FieldError id="error-starts-at" message={errors.starts_at} />
        </label>
        <label className={LABEL}>
          Fim
          <input type="datetime-local" value={endsAt} onChange={(event) => setEndsAt(event.target.value)}
            aria-invalid={Boolean(errors.ends_at)} aria-describedby="error-ends-at" className={INPUT} />
          <FieldError id="error-ends-at" message={errors.ends_at} />
        </label>
      </div>

      <label className={LABEL}>
        Descrição do exemplar
        <textarea rows={3} maxLength={1000} value={description} onChange={(event) => setDescription(event.target.value)}
          placeholder="Estado de conservação, encadernação, observações"
          className="resize-y rounded-md border border-line bg-paper px-3 py-2.5 text-sm leading-normal font-normal text-ink" />
        <span className="self-end text-xs font-normal text-muted">{description.length}/1000</span>
      </label>

      <p className="text-[13px] leading-normal text-muted">
        Título, autor, ano e capa são copiados para o nosso banco ao publicar. Se a Open Library cair, o
        lote continua funcionando.
      </p>

      {(errors.form || errors.book) && (
        <p role="alert" className="rounded-md border border-red bg-red-soft px-3.5 py-3 text-sm">
          {errors.form ?? "Não foi possível usar este livro. Escolha outro resultado da busca."}
        </p>
      )}

      <button type="submit" disabled={!book || submitting}
        className="h-12 rounded-md bg-gold-dark text-base font-semibold text-paper disabled:cursor-not-allowed disabled:opacity-60">
        {buttonLabel}
      </button>

      {notice && (
        <p role="status" className="rounded-md border border-green bg-green-soft px-3.5 py-3 text-sm font-semibold text-green">
          {notice}
        </p>
      )}
    </form>
  );
}
