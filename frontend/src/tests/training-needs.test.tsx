import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import TrainingCaseDetailPage from "@/app/dossiers/[id]/page";
import { calculateDesiredEndDate, TrainingNeedSection } from "@/components/training-need-section";
import { renderWithQueryClient } from "@/tests/test-utils";

vi.mock("next/navigation", () => ({
  useParams: () => ({ id: "case-1" }),
  usePathname: () => "/dossiers/case-1",
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
}));

const need = {
  id: "need-1",
  training_case_id: "case-1",
  target_audience: "Responsables RH",
  level: "INTERMEDIATE",
  location: "Sur site",
  participant_count: 12,
  delivery_mode: "PRESENTIEL",
  duration_hours: 21,
  planned_days_count: 3,
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
  it("calcule une fin inclusive pour un ou trois jours et ignore les valeurs invalides", () => {
    expect(calculateDesiredEndDate("2026-09-23", 1)).toBe("2026-09-23");
    expect(calculateDesiredEndDate("2026-09-23", 3)).toBe("2026-09-25");
    expect(calculateDesiredEndDate("", 3)).toBeNull();
    expect(calculateDesiredEndDate("2026-02-30", 3)).toBeNull();
    expect(calculateDesiredEndDate("2026-09-23", 0)).toBeNull();
  });

  it("recalcule la fin quand le début ou le nombre de jours change", async () => {
    const user = userEvent.setup();
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(
      new Response(JSON.stringify(need), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    ));
    renderWithQueryClient(<TrainingNeedSection caseId="case-1" onChanged={vi.fn()} />);

    const start = await screen.findByLabelText("Début souhaité");
    const days = screen.getByLabelText("Nombre de jours planifiés");
    const duration = screen.getByLabelText("Durée de la formation en heures");
    const end = screen.getByLabelText("Fin souhaitée");
    expect(duration).toHaveAttribute("min", "1");
    expect(duration).toHaveAttribute("step", "1");
    expect(end).toHaveAttribute("readonly");

    await user.clear(start);
    expect(end).toHaveValue("");
    await user.type(start, "2026-09-23");
    expect(end).toHaveValue("2026-09-25");
    await user.clear(days);
    expect(end).toHaveValue("");
    await user.type(days, "1");
    expect(end).toHaveValue("2026-09-23");
    await user.clear(days);
    await user.type(days, "3");
    expect(end).toHaveValue("2026-09-25");
  });

  it("n’affiche plus les anciennes actions de brouillon", async () => {
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
    expect(screen.queryByRole("button", { name: "Enregistrer le brouillon" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Annuler les modifications" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "← Retour" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Enregistrer et générer le programme" })).toBeInTheDocument();
  });

  it("encadre les champs obligatoires manquants et place le focus sur le premier", async () => {
    const user = userEvent.setup();
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ ...need, location: null, objectives: "" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    ));
    renderWithQueryClient(<TrainingNeedSection caseId="case-1" onChanged={vi.fn()} />);

    await screen.findByDisplayValue("Responsables RH");
    await user.click(screen.getByRole("button", { name: "Enregistrer et générer le programme" }));

    const location = screen.getByLabelText("Lieu");
    const objectives = screen.getByLabelText("Objectifs pédagogiques");
    expect(location).toHaveAttribute("aria-invalid", "true");
    expect(objectives).toHaveAttribute("aria-invalid", "true");
    expect(screen.getByLabelText("Public cible")).toHaveAttribute("aria-invalid", "false");
    expect(screen.getByRole("alert")).toHaveTextContent(
      "Champs obligatoires manquants : Lieu, Objectifs pédagogiques.",
    );
    expect(location).toHaveFocus();
  });

  it("encadre le nombre de participants quand il n’est pas un entier", async () => {
    const user = userEvent.setup();
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(
      new Response(JSON.stringify(need), { status: 200, headers: { "Content-Type": "application/json" } }),
    ));
    renderWithQueryClient(<TrainingNeedSection caseId="case-1" onChanged={vi.fn()} />);

    const participants = await screen.findByLabelText("Nombre de participants");
    await user.clear(participants);
    await user.type(participants, "10.5");
    await user.click(screen.getByRole("button", { name: "Enregistrer et générer le programme" }));

    expect(participants).toHaveAttribute("step", "1");
    expect(participants).toHaveAttribute("aria-invalid", "true");
    expect(participants).toHaveFocus();
    expect(screen.getByRole("alert")).toHaveTextContent("Valeur invalide : Nombre de participants.");
  });

  it("enregistre les modifications visibles avant de valider", async () => {
    const user = userEvent.setup();
    const updatedNeed = { ...need, location: "Sousse" };
    const validatedNeed = { ...updatedNeed, is_validated: true, validated_at: "2026-09-17T10:00:00Z" };
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(new Response(JSON.stringify(need), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify(updatedNeed), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify(validatedNeed), { status: 200 }))
      .mockResolvedValue(new Response(JSON.stringify(validatedNeed), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    renderWithQueryClient(<TrainingNeedSection caseId="case-1" onChanged={vi.fn()} />);

    const location = await screen.findByLabelText("Lieu");
    await user.clear(location);
    await user.type(location, "Sousse");
    await user.click(screen.getByRole("button", { name: "Enregistrer et générer le programme" }));

    await waitFor(() => {
      const calls = fetchMock.mock.calls.map((call) => call[1]?.method);
      expect(calls).toContain("PATCH");
      expect(calls).toContain("POST");
      expect(calls.indexOf("PATCH")).toBeLessThan(calls.indexOf("POST"));
    });
  });

  it("charge, valide et génère sans confirmation navigateur", async () => {
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
      .mockImplementation(() => Promise.resolve(
        new Response(JSON.stringify(validated), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      ));
    vi.stubGlobal("fetch", fetchMock);
    renderWithQueryClient(<TrainingNeedSection caseId="case-1" onChanged={vi.fn()} />);

    expect(await screen.findByDisplayValue("Responsables RH")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Enregistrer et générer le programme" }));
    expect(await screen.findByText(/Validé le/)).toBeInTheDocument();
    expect(screen.getByLabelText("Public cible")).toBeDisabled();
    expect(screen.queryByRole("button", { name: "Enregistrer et générer le programme" })).not.toBeInTheDocument();
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
    await user.click(screen.getByRole("button", { name: "Enregistrer et générer le programme" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Erreur de sauvegarde.");
    expect(location).toHaveValue("Nouveau lieu");
  });

  it("affiche le champ concerné quand FastAPI refuse une valeur", async () => {
    const user = userEvent.setup();
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce(new Response(JSON.stringify(need), { status: 200 }))
        .mockResolvedValueOnce(
          new Response(
            JSON.stringify({ detail: [{ loc: ["body", "duration_hours"], msg: "invalid" }] }),
            { status: 422, headers: { "Content-Type": "application/json" } },
          ),
        ),
    );
    renderWithQueryClient(<TrainingNeedSection caseId="case-1" onChanged={vi.fn()} />);

    await screen.findByLabelText("Durée de la formation en heures");
    await user.click(screen.getByRole("button", { name: "Enregistrer et générer le programme" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Valeur invalide : Durée de la formation.",
    );
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
    expect(needStep).toHaveClass("locked");
    expect(screen.getAllByText("Formateur")[0].closest("li")).toHaveClass("current");
  });

  it("ne repropose jamais un formateur déjà accepté et continue vers le besoin", async () => {
    const acceptedCase = { ...trainingCase, status: "FORMATEUR_ACCEPTE" };
    const fetchMock = vi.fn((url: string) => {
      const body = url.includes("/api/companies")
        ? { items: [], total: 0, page: 1, page_size: 10 }
        : acceptedCase;
      return Promise.resolve(
        new Response(JSON.stringify(body), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      );
    });
    vi.stubGlobal("fetch", fetchMock);
    renderWithQueryClient(<TrainingCaseDetailPage />);

    expect(await screen.findByText("Formateur accepté")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Marquer le formateur comme proposé" }))
      .not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Ouvrir le besoin client" }))
      .toBeInTheDocument();
    expect(screen.getByText("Besoin").closest("li")).toHaveClass("current");
    expect(screen.getAllByText("Formateur")[0].closest("li")).toHaveClass("completed");
  });

  it("place un besoin validé sur l’accord de principe et autorise le programme", async () => {
    const completedCase = { ...trainingCase, status: "BESOIN_COMPLETE" };
    const fetchMock = vi.fn((url: string) => {
      const body = url.includes("/api/companies")
        ? { items: [], total: 0, page: 1, page_size: 10 }
        : url.includes("/need")
          ? { ...need, is_validated: true, validated_at: "2026-07-24T13:00:00Z" }
          : completedCase;
      return Promise.resolve(
        new Response(JSON.stringify(body), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      );
    });
    vi.stubGlobal("fetch", fetchMock);
    renderWithQueryClient(<TrainingCaseDetailPage />);

    await screen.findByText("Accord de principe");
    expect(screen.queryByRole("button", { name: "Continuer vers le programme" }))
      .not.toBeInTheDocument();
    expect(screen.getByText("Accord de principe").closest("li")).toHaveClass("current");
    expect(screen.getByText("Besoin").closest("li")).toHaveClass("completed");
  });
});
