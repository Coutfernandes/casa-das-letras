/** Campo de texto com rótulo e mensagem de erro, no estilo do protótipo. */

import { useId, type InputHTMLAttributes, type ReactNode } from "react";

type TextFieldProps = InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  error?: string;
  /** Elemento dentro do campo, à direita (por exemplo, o botão de mostrar senha). */
  endAdornment?: ReactNode;
};

export function TextField({ label, error, endAdornment, id, ...inputProps }: TextFieldProps) {
  const generatedId = useId();
  const inputId = id ?? generatedId;
  const errorId = `${inputId}-error`;

  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={inputId} className="text-sm font-semibold">
        {label}
      </label>
      <div className="relative">
        <input
          id={inputId}
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? errorId : undefined}
          className={`h-11.5 w-full rounded-md border border-line bg-surface px-3.5 text-[15px] text-ink outline-offset-2 aria-invalid:border-red ${endAdornment ? "pr-12" : ""}`}
          {...inputProps}
        />
        {endAdornment && (
          <div className="absolute inset-y-0 right-1 flex items-center">{endAdornment}</div>
        )}
      </div>
      {error && (
        <p id={errorId} className="text-sm text-red">
          {error}
        </p>
      )}
    </div>
  );
}
