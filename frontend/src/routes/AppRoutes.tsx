import { BrowserRouter, Route, Routes } from "react-router-dom";

import { DashboardPage } from "../pages/Dashboard/DashboardPage";
import { LoginPage } from "../pages/Login/LoginPage";

export function AppRoutes() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LoginPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
      </Routes>
    </BrowserRouter>
  );
}