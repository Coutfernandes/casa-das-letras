/** Protege uma tela: só deixa entrar quem está logado com o papel exigido. */

import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router";

import { useAuth } from "../hooks/useAuth";
import type { Role } from "../types/user";

type RequireRoleProps = {
  role: Role;
  children: ReactNode;
};

export function RequireRole({ role, children }: RequireRoleProps) {
  const { user, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return <p className="text-muted">Conferindo a sessão...</p>;
  }
  if (!user) {
    // Depois do login, a tela de entrar devolve a pessoa para cá.
    return <Navigate to="/entrar" replace state={{ from: location.pathname }} />;
  }
  if (user.role !== role) {
    return (
      <section className="space-y-3">
        <h1 className="font-serif text-4xl font-bold">Acesso restrito</h1>
        <p className="text-muted">
          Esta área é só para {role === "AUCTIONEER" ? "leiloeiros" : "licitantes"}.
        </p>
      </section>
    );
  }
  return children;
}
