import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import TrainersPage from "@/app/formateurs/page";
import { renderWithQueryClient } from "@/tests/test-utils";

vi.mock("next/navigation", () => ({
  usePathname: () => "/formateurs",
  useRouter: () => ({ replace: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
}));

afterEach(() => vi.unstubAllGlobals());

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

  it("ouvre le formulaire de création manuelle", async () => {
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
    await userEvent.click(screen.getByRole("button", { name: "Nouveau formateur" }));
    expect(screen.getByText("Créer manuellement un formateur")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Créer le formateur" })).toBeInTheDocument();
  });
});
