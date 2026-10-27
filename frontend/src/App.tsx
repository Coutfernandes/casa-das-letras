/** Mapa de telas da aplicação. */

import { BrowserRouter, Route, Routes } from "react-router";

import { ComingSoon } from "./components/ComingSoon";
import { Layout } from "./components/Layout";
import { RequireRole } from "./components/RequireRole";
import { LoginPage } from "./features/auth/LoginPage";
import { DashboardPage } from "./features/dashboard/DashboardPage";
import { ShowcasePage } from "./features/showcase/ShowcasePage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Tela de login em tela cheia, sem o cabeçalho (como no protótipo). */}
        <Route path="entrar" element={<LoginPage />} />

        {/* Telas com o cabeçalho. */}
        <Route element={<Layout />}>
          <Route index element={<ShowcasePage />} />
          <Route path="lotes/:lotId" element={<ComingSoon title="Sala do lote" part={9} />} />
          <Route path="auditoria/:lotId" element={<ComingSoon title="Auditoria" part={11} />} />
          <Route path="comprovante/:token" element={<ComingSoon title="Comprovante" part={10} />} />

          <Route
            path="painel"
            element={
              <RequireRole role="AUCTIONEER">
                <DashboardPage />
              </RequireRole>
            }
          />
          <Route
            path="carteira"
            element={
              <RequireRole role="BIDDER">
                <ComingSoon title="Carteira" part={8} />
              </RequireRole>
            }
          />
          <Route
            path="meus-arremates"
            element={
              <RequireRole role="BIDDER">
                <ComingSoon title="Meus arremates" part={10} />
              </RequireRole>
            }
          />

          <Route path="*" element={<ComingSoon title="Página não encontrada" part={0} />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
