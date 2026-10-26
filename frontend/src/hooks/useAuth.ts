/** Acesso ao usuário logado e às ações de login, cadastro e logout. */

import { useContext } from "react";

import { AuthContext } from "../context/auth-context";

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth precisa ser usado dentro de <AuthProvider>.");
  }
  return context;
}