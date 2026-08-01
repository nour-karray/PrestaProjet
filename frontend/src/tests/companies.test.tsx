import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import CompaniesPage from "@/app/entreprises/page";
import NewCompanyPage from "@/app/entreprises/nouvelle/page";
import { renderWithQueryClient } from "@/tests/test-utils";

const { pushMock } = vi.hoisted(() => ({ pushMock: vi.fn() }));

vi.mock("next/navigation", () => ({
  usePathname: () => "/entreprises",
  useRouter: () => ({ push: pushMock, replace: vi.fn() }),
}));

afterEach(() => {
  pushMock.mockReset();
  vi.unstubAllGlobals();
});

describe("Gestion des entreprises", () => {
  it("affiche la liste et recherche par nom", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          items: [
            {
              id: "company-1",
              name: "ABC Conseil",
              address: null,
              city: "Tunis",
              postal_code: null,
              country: "Tunisie",
              tax_identifier: null,
              website: null,
              notes: null,
              is_archived: false,
              created_at: "2026-07-24T12:00:00Z",
              updated_at: "2026-07-24T12:00:00Z",
              primary_contact: {
                full_name: "Ahmed",
                email: "ahmed@formation.local",
              },
            },
          ],
          total: 1,
          page: 1,
          page_size: 10,
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );
    vi.stubGlobal("fetch", fetchMock);
    renderWithQueryClient(<CompaniesPage />);

    expect(await screen.findByText("ABC Conseil")).toBeInTheDocument();
    await user.type(screen.getByLabelText("Rechercher par nom"), "ABC");
    expect(fetchMock).toHaveBeenLastCalledWith(
      expect.stringContaining("search=ABC"),
      expect.anything(),
    );
  });

  it("affiche l’état vide", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ items: [], total: 0, page: 1, page_size: 10 }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );
    renderWithQueryClient(<CompaniesPage />);
    expect(await screen.findByText("Aucune entreprise trouvée.")).toBeInTheDocument();
  });

  it("valide puis crée une entreprise", async () => {
    const user = userEvent.setup();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ id: "company-1" }), {
          status: 201,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );
    renderWithQueryClient(<NewCompanyPage />);
    await user.click(screen.getByRole("button", { name: "Créer l’entreprise" }));
    expect(await screen.findByText("Le nom est obligatoire.")).toBeInTheDocument();
    await user.type(screen.getByLabelText("Nom"), "Nouvelle Société");
    await user.click(screen.getByRole("button", { name: "Créer l’entreprise" }));
    await waitFor(() => {
      expect(pushMock).toHaveBeenCalledWith("/entreprises/company-1");
    });
  });

  it("affiche les erreurs API", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({ code: "API_ERROR", message: "Erreur serveur." }),
          { status: 500, headers: { "Content-Type": "application/json" } },
        ),
      ),
    );
    renderWithQueryClient(<CompaniesPage />);
    expect(await screen.findByRole("alert")).toHaveTextContent("Erreur serveur.");
  });
});
