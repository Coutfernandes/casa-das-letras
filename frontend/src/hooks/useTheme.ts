/** Tema claro ou escuro, aplicado no <html> e lembrado no navegador. */

import { useCallback, useState } from "react";

type Theme = "light" | "dark";

function readTheme(): Theme {
  return document.documentElement.dataset.theme === "dark" ? "dark" : "light";
}

export function useTheme() {
  // O script do index.html já aplicou o tema certo; aqui só lemos o que está lá.
  const [theme, setTheme] = useState<Theme>(readTheme);

  const toggleTheme = useCallback(() => {
    const next: Theme = theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    try {
      localStorage.setItem("theme", next);
    } catch {
      // Sem localStorage (alguns modos privados), o tema vale só até fechar a aba.
    }
    setTheme(next);
  }, [theme]);

  return { theme, toggleTheme };
}
