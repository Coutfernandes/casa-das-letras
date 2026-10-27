/** Formato do contexto de autenticação, usado pelo AuthProvider e pelo useAuth. */

import { createContext } from "react";

import type { Credentials, Registration } from "../services/auth";
import type { User } from "../types/user";

export type AuthContextValue = {
  /** Usuário logado, ou null para visitantes. */
  user: User | null;
  /** Verdadeiro enquanto a sessão é conferida, logo que a aplicação abre. */
  isLoading: boolean;
  signIn: (credentials: Credentials) => Promise<User>;
  signUp: (registration: Registration) => Promise<User>;
  signOut: () => Promise<void>;
};

export const AuthContext = createContext<AuthContextValue | null>(null);
