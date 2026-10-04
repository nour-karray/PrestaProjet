import { Navigate, Route, Routes } from "react-router-dom";

import CompaniesPage from "@/pages/companies-page";
import CompanyDetailPage from "@/pages/company-detail-page";
import DashboardPage from "@/pages/dashboard-page";
import HomePage from "@/pages/home-page";
import ImportCvPage from "@/pages/import-cv-page";
import LoginPage from "@/pages/login-page";
import NewCompanyPage from "@/pages/new-company-page";
import NewTrainingCasePage from "@/pages/new-training-case-page";
import TrainerDetailPage from "@/pages/trainer-detail-page";
import TrainersPage from "@/pages/trainers-page";
import TrainingCaseDetailPage from "@/pages/training-case-detail-page";
import TrainingCasesPage from "@/pages/training-cases-page";
import { ProtectedRoute } from "@/router/protected-route";

export const protectedPaths = ["/tableau-de-bord", "/entreprises", "/formateurs", "/dossiers"] as const;

export default function App() {
  return <Routes>
    <Route path="/" element={<HomePage />} />
    <Route path="/connexion" element={<LoginPage />} />
    <Route element={<ProtectedRoute />}>
      <Route path="/tableau-de-bord" element={<DashboardPage />} />
      <Route path="/entreprises" element={<CompaniesPage />} />
      <Route path="/entreprises/nouvelle" element={<NewCompanyPage />} />
      <Route path="/entreprises/:id" element={<CompanyDetailPage />} />
      <Route path="/formateurs" element={<TrainersPage />} />
      <Route path="/formateurs/import-cv" element={<ImportCvPage />} />
      <Route path="/formateurs/:id" element={<TrainerDetailPage />} />
      <Route path="/dossiers" element={<TrainingCasesPage />} />
      <Route path="/dossiers/nouveau" element={<NewTrainingCasePage />} />
      <Route path="/dossiers/:id" element={<TrainingCaseDetailPage />} />
    </Route>
    <Route path="*" element={<Navigate to="/" replace />} />
  </Routes>;
}
