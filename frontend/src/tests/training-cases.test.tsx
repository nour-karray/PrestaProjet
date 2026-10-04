import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import TrainingCaseDetailPage from "@/pages/training-case-detail-page";
import NewTrainingCasePage from "@/pages/new-training-case-page";
import TrainingCasesPage from "@/pages/training-cases-page";
import { renderWithQueryClient } from "@/tests/test-utils";

const { pushMock } = vi.hoisted(() => ({ pushMock: vi.fn() }));

vi.mock("@/router/navigation", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@/router/navigation")>()),
  useParams: () => ({ id: "case-1" }),
  usePathname: () => "/dossiers",
  useRouter: () => ({ push: pushMock, replace: vi.fn() }),
}));

const companyList = {
  items: [{ id: "company-1", name: "ABC Conseil", address: null, city: "Tunis", postal_code: null, country: "Tunisie", tax_identifier: null, website: null, notes: null, is_archived: false, created_at: "2026-07-24T12:00:00Z", updated_at: "2026-07-24T12:00:00Z", primary_contact: null }],
  total: 1,
  page: 1,
  page_size: 10,
};
const trainingCatalog = [
  { id: "catalog-1", category: "Management", title: "Management", is_active: true },
  { id: "catalog-2", category: "Cybersécurité", title: "Cybersécurité", is_active: true },
];
const trainingCase = {
  id: "case-1",
  reference: "TR-2026-000001",
  company: { id: "company-1", name: "ABC Conseil" },
  primary_contact: null,
  theme: "Audit RH",
  description: null,
  status: "BROUILLON",
  desired_start_date: null,
  desired_end_date: null,
  created_at: "2026-07-24T12:00:00Z",
  updated_at: "2026-07-24T12:00:00Z",
  closed_at: null,
  is_archived: false,
};

afterEach(() => {
  pushMock.mockReset();
  vi.unstubAllGlobals();
});

describe("Gestion des dossiers", () => {
  it("affiche la liste et ses filtres", async () => {
    vi.stubGlobal("fetch", vi.fn((url: string) => Promise.resolve(new Response(JSON.stringify(url.includes("/api/companies") ? companyList : { items: [trainingCase], total: 1, page: 1, page_size: 10 }), { status: 200, headers: { "Content-Type": "application/json" } }))));
    renderWithQueryClient(<TrainingCasesPage />);
    expect(await screen.findByText("TR-2026-000001")).toBeInTheDocument();
    expect(screen.getByLabelText("Statut")).toBeInTheDocument();
  });

  it("valide le thème, charge les contacts et crée le dossier", async () => {
    const user = userEvent.setup();
    const contact = { id: "contact-1", company_id: "company-1", full_name: "Contact principal", email: null, phone: null, job_title: null, is_primary: true, created_at: "2026-07-24T12:00:00Z", updated_at: "2026-07-24T12:00:00Z" };
    vi.stubGlobal("fetch", vi.fn((url: string, options?: RequestInit) => {
      const body = url.includes("/api/training-catalog") ? trainingCatalog : options?.method === "POST" ? trainingCase : url.endsWith("/api/companies/company-1") ? { ...companyList.items[0], contacts: [contact] } : companyList;
      return Promise.resolve(new Response(JSON.stringify(body), { status: options?.method === "POST" ? 201 : 200, headers: { "Content-Type": "application/json" } }));
    }));
    const { container } = renderWithQueryClient(<NewTrainingCasePage />);
    expect(screen.getByRole("button", { name: "Créer le dossier" })).toBeDisabled();
    expect(screen.queryByRole("button", { name: "Enregistrer comme brouillon" })).not.toBeInTheDocument();
    await user.type(screen.getByRole("combobox", { name: /Entreprise/ }), "AB");
    expect(await screen.findByRole("option", { name: /ABC Conseil/ })).toBeInTheDocument();
    await user.click(screen.getByRole("option", { name: /ABC Conseil/ }));
    const contactCombobox = screen.getByRole("combobox", { name: /Personne/ });
    await waitFor(() => expect(contactCombobox).toBeEnabled(), { timeout: 5_000 });
    await user.click(contactCombobox);
    expect(await screen.findByRole("option", { name: /Contact principal/ })).toBeInTheDocument();
    await user.selectOptions(screen.getByLabelText("Thème"), "Management");
    expect(container.querySelectorAll("optgroup")).toHaveLength(0);
    expect(screen.getByText("(facultatif)")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Créer le dossier" }));
    expect(await screen.findByText("Dossier créé avec succès")).toBeInTheDocument();
    expect(screen.getByText("TR-2026-000001")).toBeInTheDocument();
  });

  it("affiche les sociétés existantes dès l’ouverture du champ entreprise", async () => {
    vi.stubGlobal("fetch", vi.fn((url: string) => Promise.resolve(new Response(JSON.stringify(url.includes("/api/training-catalog") ? trainingCatalog : companyList), { status: 200, headers: { "Content-Type": "application/json" } }))));
    renderWithQueryClient(<NewTrainingCasePage />);
    await userEvent.click(screen.getByRole("combobox", { name: /Entreprise/ }));
    expect(await screen.findByText("Sociétés déjà enregistrées")).toBeInTheDocument();
    expect(await screen.findByRole("option", { name: /ABC Conseil/ })).toBeInTheDocument();
  });

  it("affiche le détail, change le statut, annule et montre l’historique", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.fn((url: string, options?: RequestInit) => {
      let body: unknown = trainingCase;
      if (url.includes("/activity")) body = [{ id: "activity-1", action: "CREATION", details: {}, created_at: "2026-07-24T12:00:00Z" }];
      else if (url.includes("/api/companies")) body = companyList;
      else if (options?.method === "POST" && url.includes("change-status")) body = { ...trainingCase, status: "DEMANDE_RECUE" };
      else if (options?.method === "POST" && url.includes("cancel")) body = { ...trainingCase, status: "ANNULE" };
      return Promise.resolve(new Response(JSON.stringify(body), { status: 200, headers: { "Content-Type": "application/json" } }));
    });
    vi.stubGlobal("fetch", fetchMock);
    renderWithQueryClient(<TrainingCaseDetailPage />);
    expect(await screen.findByText("TR-2026-000001")).toBeInTheDocument();
    expect(screen.queryByText("CREATION")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Voir l’historique" }));
    expect(await screen.findByText("CREATION")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Masquer l’historique" })).toHaveAttribute("aria-expanded", "true");
    await user.click(screen.getByRole("button", { name: /Passer à/ }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("change-status"), expect.anything()));
    await user.click(screen.getByRole("button", { name: "Annuler le dossier" }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/cancel"), expect.anything()));
  });

  it("affiche une erreur API", async () => {
    vi.stubGlobal("fetch", vi.fn().mockImplementation(() => Promise.resolve(new Response(JSON.stringify({ code: "API_ERROR", message: "Erreur serveur." }), { status: 500, headers: { "Content-Type": "application/json" } }))));
    renderWithQueryClient(<TrainingCasesPage />);
    expect(await screen.findByRole("alert")).toHaveTextContent("Erreur serveur.");
  });
});
