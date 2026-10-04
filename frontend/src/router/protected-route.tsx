import { useQuery } from "@tanstack/react-query";
import { Navigate, Outlet, useLocation } from "react-router-dom";

import { getCurrentAdministrator } from "@/features/auth/api";

export function ProtectedRoute() {
  const location = useLocation();
  const account = useQuery({
    queryKey: ["auth", "me"],
    queryFn: getCurrentAdministrator,
    retry: false,
    staleTime: 60_000,
  });

  if (account.isPending) return <div className="loading-state" role="status">Vérification de la session…</div>;
  if (account.isError) return <Navigate to="/connexion" replace state={{ from: location.pathname }} />;
  return <Outlet />;
}
