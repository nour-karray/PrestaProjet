import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import CompanyDetailPage from "@/pages/company-detail-page";
import { renderWithQueryClient } from "@/tests/test-utils";

vi.mock("@/router/navigation", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@/router/navigation")>()),
  useParams: () => ({ id: "company-1" }),
  usePathname: () => "/entreprises/company-1",
  useRouter: () => ({ replace: vi.fn() }),
}));

afterEach(() => vi.unstubAllGlobals());

describe("Détail d’une entreprise", () => {
  it("affiche le détail, ajoute un contact et permet de le définir principal", async () => {
    const user = userEvent.setup();
    const company = {
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
      contacts: [],
    };
    const contact = {
      id: "contact-1",
      company_id: "company-1",
      full_name: "Nouveau Contact",
      email: null,
      phone: null,
      job_title: null,
      is_primary: false,
      created_at: "2026-07-24T12:00:00Z",
      updated_at: "2026-07-24T12:00:00Z",
    };
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce(
          new Response(JSON.stringify(company), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          }),
        )
        .mockResolvedValueOnce(
          new Response(JSON.stringify(contact), {
            status: 201,
            headers: { "Content-Type": "application/json" },
          }),
        )
        .mockResolvedValue(
          new Response(JSON.stringify({ ...company, contacts: [contact] }), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          }),
        ),
    );
    renderWithQueryClient(<CompanyDetailPage />);

    expect(
      await screen.findByRole("heading", { name: "ABC Conseil" }),
    ).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Ajouter" }));
    await user.type(screen.getAllByLabelText("Nom")[1], "Nouveau Contact");
    await user.click(
      screen.getByRole("button", { name: /^Enregistrer$/ }),
    );

    expect(await screen.findByText("Nouveau Contact")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Définir comme principal" }),
    ).toBeInTheDocument();
  });
});
