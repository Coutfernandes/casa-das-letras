/** Tela de entrar e criar conta, em tela cheia, como no protótipo. */

import { useState, type FormEvent } from "react";
import { Link, Navigate, useLocation } from "react-router";

import { TextField } from "../../components/TextField";
import { ThemeToggle } from "../../components/ThemeToggle";
import { useAuth } from "../../hooks/useAuth";
import { toFieldErrors, type FieldErrors } from "../../services/errors";
import type { Role, User } from "../../types/user";
import { PasswordField } from "../../components/PasswordField";

type Mode = "login" | "signup";

const SPINE_COLORS = ["#5B3A29", "#2F4A3A", "#6B2E2A", "#4A3B5C", "#B47B32"];

const ROLE_OPTIONS: { role: Role; label: string; note: string }[] = [
  { role: "BIDDER", label: "Licitante", note: "Deposita saldo, dá lances e arremata." },
  { role: "AUCTIONEER", label: "Leiloeiro", note: "Cria e gerencia lotes. Não dá lances." },
];

const SEED_PASSWORD = "SenhaSegura123!";
const SEED_ACCOUNTS = [
  "leiloeiro@casadasletras.com",
  "licitante1@casadasletras.com",
  "licitante2@casadasletras.com",
];

/** Depois de entrar: volta para onde a pessoa estava, ou vai para a tela do papel. */
function destinationFor(user: User, from?: string) {
  if (from) return from;
  return user.role === "AUCTIONEER" ? "/painel" : "/";
}

function BrandPanel() {
  return (
    <section className="flex flex-[1_1_460px] flex-col justify-between gap-12 bg-[#24251f] px-12 py-14 text-[#f3efe6]">
      <div className="flex flex-col">
        <span className="font-serif text-[28px] font-bold">Casa das Letras</span>
        <span className="text-xs tracking-[0.14em] text-[#bdb6a6] uppercase">
          Leilões de livros raros
        </span>
      </div>

      <div className="max-w-115">
        <h1 className="font-serif text-5xl leading-[1.08] font-bold">
          Lances ao vivo, histórico à prova de adulteração.
        </h1>
        <p className="mt-4.5 text-[17px] leading-relaxed text-[#d5cfc1]">
          Livros raros catalogados pela Open Library. Leiloeiros publicam lotes, licitantes
          disputam com saldo simulado e qualquer pessoa pode auditar o resultado.
        </p>
      </div>

      <div aria-hidden="true" className="flex gap-3">
        {SPINE_COLORS.map((color) => (
          <span
            key={color}
            className="h-19 w-13.5 rounded-[1px_3px_3px_1px] shadow-[inset_3px_0_0_rgb(0_0_0/0.25)]"
            style={{ backgroundColor: color }}
          />
        ))}
      </div>
    </section>
  );
}

export function LoginPage() {
  const { user, signIn, signUp } = useAuth();
  const location = useLocation();
  const from = (location.state as { from?: string } | null)?.from;

  const [mode, setMode] = useState<Mode>("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<Role>("BIDDER");
  const [errors, setErrors] = useState<FieldErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Já logado (ou acabou de entrar): segue para a tela certa.
  if (user) {
    return <Navigate to={destinationFor(user, from)} replace />;
  }

  const isSignup = mode === "signup";

  function switchMode(next: Mode) {
    setMode(next);
    setErrors({});
  }

  function fillSeedAccount(seedEmail: string) {
    switchMode("login");
    setEmail(seedEmail);
    setPassword(SEED_PASSWORD);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrors({});
    setIsSubmitting(true);
    try {
      if (isSignup) {
        await signUp({ name, email, password, role });
      } else {
        await signIn({ email, password });
      }
    } catch (error) {
      setErrors(toFieldErrors(error));
      setIsSubmitting(false);
    }
  }

  const tabClass = (active: boolean) =>
    `h-10.5 rounded-sm text-[15px] font-semibold ${active ? "bg-paper" : "bg-transparent text-muted"}`;

  return (
    <div className="flex min-h-screen flex-wrap bg-paper text-ink">
      <BrandPanel />

      <section className="flex flex-[1_1_460px] items-center justify-center px-12 py-14">
        <div className="flex w-full max-w-105 flex-col gap-5">
          <div className="flex justify-end">
            <ThemeToggle />
          </div>

          <div
            role="tablist"
            aria-label="Acesso"
            className="grid grid-cols-2 rounded-md border border-line bg-surface p-1"
          >
            <button type="button" role="tab" aria-selected={!isSignup} onClick={() => switchMode("login")} className={tabClass(!isSignup)}>
              Entrar
            </button>
            <button type="button" role="tab" aria-selected={isSignup} onClick={() => switchMode("signup")} className={tabClass(isSignup)}>
              Criar conta
            </button>
          </div>

          <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-3.5">
            {errors.form && (
              <p role="alert" className="rounded-md border border-red bg-red-soft px-3.5 py-3 text-[15px] font-medium text-red">
                {errors.form}
              </p>
            )}

            {isSignup && (
              <TextField
                label="Nome"
                autoComplete="name"
                value={name}
                onChange={(event) => setName(event.target.value)}
                error={errors.name}
                required
              />
            )}
            <TextField
              label="E-mail"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              error={errors.email}
              required
            />
            <PasswordField
              label="Senha"
              autoComplete={isSignup ? "new-password" : "current-password"}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              error={errors.password}
              required
            />

            {isSignup && (
              <fieldset className="flex flex-col gap-2">
                <legend className="mb-2 text-sm font-semibold">Como você vai usar</legend>
                {ROLE_OPTIONS.map((option) => {
                  const selected = role === option.role;
                  return (
                    <label
                      key={option.role}
                      className={`flex cursor-pointer items-start gap-3 rounded-md border px-3.5 py-3 ${selected ? "border-gold bg-gold-soft" : "border-line bg-surface"}`}
                    >
                      <input
                        type="radio"
                        name="role"
                        value={option.role}
                        checked={selected}
                        onChange={() => setRole(option.role)}
                        className="mt-1 accent-gold-dark"
                      />
                      <span className="flex flex-col gap-0.5">
                        <span className="text-[15px] font-semibold">{option.label}</span>
                        <span className="text-[13px] text-muted">{option.note}</span>
                      </span>
                    </label>
                  );
                })}
                {errors.role && <p className="text-sm text-red">{errors.role}</p>}
              </fieldset>
            )}

            <button
              type="submit"
              disabled={isSubmitting}
              className="h-12 rounded-md bg-gold-dark text-base font-semibold text-paper disabled:opacity-60"
            >
              {isSubmitting ? "Aguarde..." : isSignup ? "Criar conta" : "Entrar"}
            </button>
          </form>

          {!isSignup && (
            <div className="flex flex-col gap-2.5 rounded-md border border-line bg-surface p-4">
              <p className="text-sm leading-normal">
                Não precisa de conta para acompanhar lotes ou verificar se um histórico de lances
                foi adulterado.
              </p>
              <div className="flex flex-wrap gap-x-5 gap-y-2 text-sm font-semibold">
                <Link to="/" className="py-1 text-gold-dark hover:text-ink">
                  Ver vitrine sem entrar
                </Link>
                <Link to="/" className="py-1 text-gold-dark hover:text-ink">
                  Auditar um lote
                </Link>
              </div>
            </div>
          )}

          <div className="flex flex-col gap-2 rounded-md border border-dashed border-line p-4">
            <span className="text-[13px] font-semibold">Contas de teste (seed)</span>
            <ul className="flex flex-col font-mono text-[13px] leading-relaxed">
              {SEED_ACCOUNTS.map((seedEmail) => (
                <li key={seedEmail}>
                  <button
                    type="button"
                    onClick={() => fillSeedAccount(seedEmail)}
                    className="text-left text-muted hover:text-gold-dark"
                  >
                    {seedEmail}
                  </button>
                </li>
              ))}
            </ul>
            <span className="font-mono text-[13px] text-muted">Senha: {SEED_PASSWORD}</span>
            <span className="text-xs text-muted">Clique numa conta para preencher o formulário.</span>
          </div>
        </div>
      </section>
    </div>
  );
}
