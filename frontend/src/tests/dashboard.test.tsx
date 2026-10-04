import { screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";

import DashboardPage from "@/pages/dashboard-page";
import { renderWithQueryClient } from "@/tests/test-utils";

vi.mock("@/router/navigation", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@/router/navigation")>()),
  useRouter: () => ({ replace: vi.fn() }),
  usePathname: () => "/tableau-de-bord",
}));

afterEach(() => vi.unstubAllGlobals());

it("affiche les indicateurs et les derniers dossiers", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          active_count: 3,
          cancelled_count: 1,
          archived_count: 2,
          recent_cases: [
            {
              id: "case-1",
              reference: "TR-2026-000001",
              company: { id: "company-1", name: "ABC Conseil" },
              primary_contact: null,
              theme: "Audit RH",
              status: "BROUILLON",
              desired_start_date: null,
              desired_end_date: null,
              created_at: "2026-07-24T12:00:00Z",
              updated_at: "2026-07-24T12:00:00Z",
              closed_at: null,
              is_archived: false,
            },
          ],
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    ),
  );
  renderWithQueryClient(<DashboardPage />);
  expect(await screen.findByText("Dossiers actifs")).toBeInTheDocument();
  expect(screen.getAllByText("TR-2026-000001")).toHaveLength(2);
});
