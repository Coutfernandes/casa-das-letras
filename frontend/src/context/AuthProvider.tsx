/** Guarda o usuário logado e oferece login, cadastro e logout para toda a aplicação. */

import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";

import * as authService from "../services/auth";
import type { Credentials, Registration } from "../services/auth";
import type { User } from "../types/user";
import { AuthContext, type AuthContextValue } from "./auth-context";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Ao abrir a aplicação: pega o cookie CSRF e descobre se já existe sessão.
  useEffect(() => {
    async function loadSession() {
      try {
        await authService.fetchCsrfCookie();
        setUser(await authService.fetchCurrentUser());
      } catch {
        // 403 = visitante sem sessão. Qualquer outro erro também deixa como visitante.
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    }
    loadSession();
  }, []);

  const signIn = useCallback(async (credentials: Credentials) => {
    const loggedUser = await authService.login(credentials);
    setUser(loggedUser);
    return loggedUser;
  }, []);

  const signUp = useCallback(async (registration: Registration) => {
    const newUser = await authService.register(registration);
    setUser(newUser);
    return newUser;
  }, []);

  const signOut = useCallback(async () => {
    await authService.logout();
    setUser(null);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ user, isLoading, signIn, signUp, signOut }),
    [user, isLoading, signIn, signUp, signOut],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
