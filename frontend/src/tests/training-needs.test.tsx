import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import TrainingCaseDetailPage from "@/app/dossiers/[id]/page";
import { TrainingNeedSection } from "@/components/training-need-section";
import { renderWithQueryClient } from "@/tests/test-utils";

vi.mock("next/navigation", () => ({
  useParams: () => ({ id: "case-1" }),
  usePathname: () => "/dossiers/case-1",
  useRouter: () => ({ replace: vi.fn() }),
}));

const need = {
  id: "need-1",
  training_case_id: "case-1",
  target_audience: "Responsables RH",
  location: "Sur site",
  participant_count: 12,
  delivery_mode: "PRESENTIEL",
  duration_hours: 21,
  objectives: "Maîtriser les techniques d’audit.",
  desired_start_date: "2026-09-01",
  desired_end_date: "2026-09-03",
  constraints: null,
  is_validated: false,
  validated_at: null,
  created_at: "2026-07-24T12:00:00Z",
  updated_at: "2026-07-24T12:00:00Z",
};

const trainingCase = {
  id: "case-1",
  reference: "TR-2026-000001",
  company: { id: "company-1", name: "ABC Conseil" },
  primary_contact: null,
  trainer: { id: "trainer-1", full_name: "Karim Ben Salah", job_title: "Consultant" },
  theme: "Audit RH",
  description: null,
  status: "RECHERCHE_FORMATEUR",
  desired_start_date: null,
  desired_end_date: null,
  created_at: "2026-07-24T12:00:00Z",
  updated_at: "2026-07-24T12:00:00Z",
  closed_at: null,
  is_archived: false,
};

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("Besoin du client", () => {
  it("affiche le formulaire et enregistre un brouillon partiel", async () => {
    const user = userEvent.setup();
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({ code: "TRAINING_NEED_NOT_FOUND", message: "Introuvable" }),
          { status: 404, headers: { "Content-Type": "application/json" } },
        ),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ ...need, location: null }), {
          status: 201,
          headers: { "Content-Type": "application/json" },
        }),
      )
      .mockResolvedValue(
        new Response(JSON.stringify({ ...need, location: null }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      );
    vi.stubGlobal("fetch", fetchMock);
    renderWithQueryClient(<TrainingNeedSection caseId="case-1" onChanged={vi.fn()} />);

    await user.type(await screen.findByLabelText("Public cible"), "Responsables RH");
    await user.click(screen.getByRole("button", { name: "Enregistrer le brouillon" }));

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining("/api/training-cases/case-1/need"),
        expect.objectContaining({ method: "POST" }),
      ),
    );
    expect(await screen.findByDisplayValue("Responsables RH")).toBeInTheDocument();
  });

  it("charge, confirme, valide puis affiche le besoin en lecture seule", async () => {
    const user = userEvent.setup();
    const validated = {
      ...need,
      is_validated: true,
      validated_at: "2026-07-24T13:00:00Z",
    };
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(JSON.stringify(need), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify(validated), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      )
      .mockResolvedValue(
        new Response(JSON.stringify(validated), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      );
    vi.stubGlobal("fetch", fetchMock);
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(true);
    renderWithQueryClient(<TrainingNeedSection caseId="case-1" onChanged={vi.fn()} />);

    expect(await screen.findByDisplayValue("Responsables RH")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Valider le besoin" }));
    expect(confirm).toHaveBeenCalledWith("Valider définitivement ce besoin client ?");
    expect(await screen.findByText(/Validé le/)).toBeInTheDocument();
    expect(screen.getByLabelText("Public cible")).toBeDisabled();
    expect(screen.queryByRole("button", { name: "Valider le besoin" })).not.toBeInTheDocument();
  });

  it("conserve les valeurs et affiche les erreurs de sauvegarde", async () => {
    const user = userEvent.setup();
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce(
          new Response(JSON.stringify(need), {
            status: 200,
            headers: { "Content-Type": "application/json" },
          }),
        )
        .mockResolvedValueOnce(
          new Response(
            JSON.stringify({ code: "API_ERROR", message: "Erreur de sauvegarde." }),
            { status: 500, headers: { "Content-Type": "application/json" } },
          ),
        ),
    );
    renderWithQueryClient(<TrainingNeedSection caseId="case-1" onChanged={vi.fn()} />);
    const location = await screen.findByLabelText("Lieu");
    await user.clear(location);
    await user.type(location, "Nouveau lieu");
    await user.click(screen.getByRole("button", { name: "Enregistrer le brouillon" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Erreur de sauvegarde.");
    expect(location).toHaveValue("Nouveau lieu");
  });

  it("expose les transitions formateur et l’état visuel Besoin", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.fn((url: string, options?: RequestInit) => {
      let body: unknown = trainingCase;
      if (url.includes("/activity")) body = [];
      if (url.includes("/api/companies")) body = { items: [], total: 0, page: 1, page_size: 10 };
      if (options?.method === "POST" && url.includes("change-status")) {
        body = { ...trainingCase, status: "FORMATEUR_PROPOSE" };
      }
      return Promise.resolve(
        new Response(JSON.stringify(body), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      );
    });
    vi.stubGlobal("fetch", fetchMock);
    renderWithQueryClient(<TrainingCaseDetailPage />);

    await user.click(
      await screen.findByRole("button", { name: "Marquer le formateur comme proposé" }),
    );
    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining("change-status"),
        expect.anything(),
      ),
    );
    const needStep = screen.getByText("Besoin").closest("li");
    expect(needStep).not.toBeNull();
    expect(needStep).toHaveClass("completed");
    expect(screen.getAllByText("Formateur")[0].closest("li")).toHaveClass("current");
  });
});
