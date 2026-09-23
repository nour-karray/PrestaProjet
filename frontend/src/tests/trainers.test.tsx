import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import TrainersPage from "@/app/formateurs/page";
import { renderWithQueryClient } from "@/tests/test-utils";

const { navigationState, pushMock } = vi.hoisted(() => ({
  navigationState: { query: "" },
  pushMock: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  usePathname: () => "/formateurs",
  useRouter: () => ({ push: pushMock, replace: vi.fn() }),
  useSearchParams: () => new URLSearchParams(navigationState.query),
}));

afterEach(() => {
  navigationState.query = "";
  pushMock.mockReset();
  vi.unstubAllGlobals();
});

describe("Gestion des formateurs", () => {
  it("recherche et affiche les formateurs disponibles", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          items: [
            {
              id: "trainer-1",
              full_name: "Karim Ben Salah",
              job_title: "Marketing digital",
              is_active: true,
              created_at: "2026-07-24T12:00:00Z",
              updated_at: "2026-07-24T12:00:00Z",
            },
          ],
          total: 1,
          page: 1,
          page_size: 20,
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );
    vi.stubGlobal("fetch", fetchMock);
    renderWithQueryClient(<TrainersPage />);

    expect(await screen.findByText("Karim Ben Salah")).toBeInTheDocument();
    await user.type(screen.getByLabelText("Rechercher un formateur"), "Karim");
    await waitFor(() =>
      expect(fetchMock).toHaveBeenLastCalledWith(
        expect.stringContaining("search=Karim"),
        expect.anything(),
      ),
    );
  });

  it("ne propose plus de création manuelle", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({ items: [], total: 0, page: 1, page_size: 20 }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      ),
    );
    renderWithQueryClient(<TrainersPage />);
    expect(screen.queryByRole("tab", { name: "Ajouter manuellement" })).not.toBeInTheDocument();
    expect(screen.queryByText("Créer manuellement un formateur")).not.toBeInTheDocument();
  });

  it("confirme le formateur puis redirige vers le besoin", async () => {
    navigationState.query = "case_id=case-1";
    const trainer = {
      id: "trainer-1",
      full_name: "Karim Ben Salah",
      job_title: "Consultant",
      city: "Tunis",
      cv_id: null,
      is_active: true,
      created_at: "2026-07-24T12:00:00Z",
      updated_at: "2026-07-24T12:00:00Z",
    };
    let status = "RECHERCHE_FORMATEUR";
    let selected = false;
    const trainingCase = () => ({
      id: "case-1",
      reference: "TR-2026-000001",
      status,
      theme: "Audit RH",
      company: { id: "company-1", name: "ABC" },
      trainer: selected ? trainer : null,
      is_archived: false,
      created_at: "2026-07-24T12:00:00Z",
      updated_at: "2026-07-24T12:00:00Z",
    });
    const fetchMock = vi.fn((url: string, options?: RequestInit) => {
      if (url.includes("/api/trainers") && !url.includes("training-cases")) {
        return Promise.resolve(new Response(JSON.stringify({ items: [trainer], total: 1, page: 1, page_size: 20 }), { status: 200, headers: { "Content-Type": "application/json" } }));
      }
      if (options?.method === "POST" && url.endsWith("/trainer")) selected = true;
      if (options?.method === "POST" && url.includes("change-status")) {
        status = JSON.parse(String(options.body)).status;
      }
      return Promise.resolve(new Response(JSON.stringify(trainingCase()), { status: 200, headers: { "Content-Type": "application/json" } }));
    });
    vi.stubGlobal("fetch", fetchMock);
    renderWithQueryClient(<TrainersPage />);

    expect(await screen.findByText("Spécialité recherchée :")).toBeInTheDocument();
    expect(screen.getByText("Type de formation du dossier")).toBeInTheDocument();
    expect(screen.getAllByText("Audit RH").length).toBeGreaterThanOrEqual(2);
    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining("specialty=Audit+RH"),
        expect.anything(),
      ),
    );
    await userEvent.click(await screen.findByRole("button", { name: "Sélectionner" }));
    const confirmButton = await screen.findByRole("button", { name: "Confirmer" });
    await waitFor(() => expect(confirmButton).toBeEnabled());
    await userEvent.click(confirmButton);

    await waitFor(() => expect(pushMock).toHaveBeenCalledWith("/dossiers/case-1?step=3&trainer=confirmed"));
    expect(status).toBe("BESOIN_A_COMPLETER");
  });
});
