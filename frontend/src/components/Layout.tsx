/** Moldura das telas: cabeçalho do protótipo e a tela atual embaixo. */

import { Link, NavLink, Outlet, useNavigate } from "react-router";

import { useAuth } from "../hooks/useAuth";
import type { User } from "../types/user";
import { ThemeToggle } from "./ThemeToggle";

const ROLE_LABEL = { AUCTIONEER: "Leiloeiro", BIDDER: "Licitante" } as const;

function navLinkClass({ isActive }: { isActive: boolean }) {
  return [
    "border-b-2 py-2.5",
    isActive ? "border-gold font-semibold text-ink" : "border-transparent text-muted hover:text-ink",
  ].join(" ");
}

/** Iniciais do nome: "Ana Souza" vira "AS"; "Bruno" vira "B". */
function initials(name: string) {
  const parts = name.trim().split(/\s+/);
  const first = parts[0]?.[0] ?? "";
  const last = parts.length > 1 ? parts[parts.length - 1][0] : "";
  return (first + last).toUpperCase();
}

function MainNav({ user }: { user: User | null }) {
  const showcase = (
    <NavLink to="/" end className={navLinkClass}>
      Vitrine
    </NavLink>
  );

  if (user?.role === "AUCTIONEER") {
    return (
      <>
        <NavLink to="/painel" className={navLinkClass}>
          Painel
        </NavLink>
        {showcase}
      </>
    );
  }
  return (
    <>
      {showcase}
      {user?.role === "BIDDER" && (
        <>
          <NavLink to="/meus-arremates" className={navLinkClass}>
            Meus arremates
          </NavLink>
          <NavLink to="/carteira" className={navLinkClass}>
            Carteira
          </NavLink>
        </>
      )}
    </>
  );
}

function UserMenu({ user, onSignOut }: { user: User; onSignOut: () => void }) {
  return (
    <>
      <div className="flex items-center gap-2.5">
        <span
          aria-hidden="true"
          className="flex size-9 items-center justify-center rounded-full border border-line bg-paper text-[13px] font-semibold"
        >
          {initials(user.name)}
        </span>
        <span className="flex flex-col text-[13px] leading-tight">
          <span className="font-semibold">{user.name}</span>
          <span className="text-muted">{ROLE_LABEL[user.role]}</span>
        </span>
      </div>
      <button
        type="button"
        onClick={onSignOut}
        className="h-11 rounded-md border border-line px-4 text-sm font-semibold text-muted hover:text-ink"
      >
        Sair
      </button>
    </>
  );
}

export function Layout() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();

  async function handleSignOut() {
    await signOut();
    navigate("/");
  }

  return (
    <div className="min-h-screen bg-paper text-ink">
      <header className="border-b border-line bg-surface">
        <div className="mx-auto flex max-w-300 flex-wrap items-center gap-x-8 gap-y-4 px-6 py-3.5">
          <Link to="/" className="flex flex-col text-ink no-underline">
            <span className="font-serif text-2xl leading-tight font-bold">Casa das Letras</span>
            <span className="text-[11px] tracking-[0.12em] text-muted uppercase">
              Leilões de livros raros
            </span>
          </Link>

          <nav aria-label="Principal" className="flex flex-auto flex-wrap gap-x-6 gap-y-1 text-[15px]">
            <MainNav user={user} />
          </nav>

          <div className="flex items-center gap-3">
            <ThemeToggle />
            {user ? (
              <UserMenu user={user} onSignOut={handleSignOut} />
            ) : (
              <Link
                to="/entrar"
                className="flex h-11 items-center rounded-md bg-gold-dark px-5 text-[15px] font-semibold text-paper"
              >
                Entrar para dar lances
              </Link>
            )}
          </div>
        </div>
      </header>

      {!user && (
        <div className="border-b border-line bg-green-soft">
          <p className="mx-auto max-w-300 px-6 py-3 text-sm">
            Você está navegando sem login. Dá para acompanhar os lotes ao vivo e auditar o
            histórico de qualquer lote; para dar lances, entre na sua conta.
          </p>
        </div>
      )}

      <main className="mx-auto max-w-300 px-6 pt-12 pb-18">
        <Outlet />
      </main>
    </div>
  );
}
