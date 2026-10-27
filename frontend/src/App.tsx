/** Mapa de telas da aplicação. */

import { BrowserRouter, Route, Routes } from "react-router";

import { ComingSoon } from "./components/ComingSoon";
import { Layout } from "./components/Layout";
import { RequireRole } from "./components/RequireRole";
import { AuctionRoomPage } from "./features/auction-room/AuctionRoomPage";
import { LoginPage } from "./features/auth/LoginPage";
import { DashboardPage } from "./features/dashboard/DashboardPage";
import { MyBidsPage } from "./features/my-bids/MyBidsPage";
import { ReceiptPage } from "./features/receipt/ReceiptPage";
import { ShowcasePage } from "./features/showcase/ShowcasePage";
import { WalletPage } from "./features/wallet/WalletPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Tela de login em tela cheia, sem o cabeçalho (como no protótipo). */}
        <Route path="entrar" element={<LoginPage />} />

        {/* Telas com o cabeçalho. */}
        <Route element={<Layout />}>
          <Route index element={<ShowcasePage />} />
          <Route path="lotes/:lotId" element={<AuctionRoomPage />} />
          <Route path="auditoria/:lotId" element={<ComingSoon title="Auditoria" part={11} />} />
          <Route path="comprovante/:token" element={<ReceiptPage />} />

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
                <WalletPage />
              </RequireRole>
            }
          />
          <Route
            path="meus-arremates"
            element={
              <RequireRole role="BIDDER">
                <MyBidsPage />
              </RequireRole>
            }
          />

          <Route path="*" element={<ComingSoon title="Página não encontrada" part={0} />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
