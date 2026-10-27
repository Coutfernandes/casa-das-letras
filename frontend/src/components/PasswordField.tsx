/** Campo de senha com botão para mostrar ou ocultar o que foi digitado. */

import { useState, type ComponentProps } from "react";

import { TextField } from "./TextField";

type PasswordFieldProps = Omit<ComponentProps<typeof TextField>, "type" | "endAdornment">;

export function PasswordField(props: PasswordFieldProps) {
  const [isVisible, setIsVisible] = useState(false);
  const toggleLabel = isVisible ? "Ocultar senha" : "Mostrar senha";

  return (
    <TextField
      {...props}
      type={isVisible ? "text" : "password"}
      autoCapitalize="none"
      spellCheck={false}
      endAdornment={
        <button
          type="button"
          onClick={() => setIsVisible((visible) => !visible)}
          aria-label={toggleLabel}
          aria-pressed={isVisible}
          title={toggleLabel}
          className="flex size-10 items-center justify-center rounded-md text-muted hover:text-ink"
        >
          <svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round">
            {isVisible ? (
              <>
                <path d="M3 3l18 18" />
                <path d="M10.6 5.1A10 10 0 0 1 12 5c6.5 0 10 7 10 7a17 17 0 0 1-3.2 4.2" />
                <path d="M6.6 6.6C3.9 8.3 2 12 2 12s3.5 7 10 7a9.7 9.7 0 0 0 5.4-1.6" />
                <path d="M9.9 9.9a3 3 0 0 0 4.2 4.2" />
              </>
            ) : (
              <>
                <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z" />
                <circle cx="12" cy="12" r="3" />
              </>
            )}
          </svg>
        </button>
      }
    />
  );
}
