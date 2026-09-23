import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { TrainingProgramSection } from "@/components/training-program-section";
import { renderWithQueryClient } from "@/tests/test-utils";

const response = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
const validNeed = { id: "need-1", training_case_id: "case-1", is_validated: true };

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("Génération assistée du programme", () => {
  it("présente la structure professionnelle, l’état vide et l’avertissement de titre", async () => {
    const user = userEvent.setup();
    const program = {
      id: "program-1", training_case_id: "case-1", title: "Gestion de projet",
      general_objectives: "Identifier les risques\nAppliquer les bons réflexes",
      prerequisites: "Aucun", evaluation_method: "Mise en situation", is_submitted: false,
      is_validated: false, submitted_at: null, validated_at: null, returned_at: null,
      return_reason: null, expected_total_minutes: 240, theory_total_minutes: 120,
      practice_total_minutes: 120, total_minutes: 240, days: [{ id: "day-1", title: "Fondamentaux",
        position: 1, theory_total_minutes: 120, practice_total_minutes: 120, total_minutes: 240,
        items: [{ id: "item-1", item_type: "MODULE", parent_id: null,
          title: "Menaces et risques", content: "Phishing\nMots de passe", theory_minutes: 60,
          practice_minutes: 30, theory_total_minutes: 60, practice_total_minutes: 30,
          total_minutes: 90, position: 1, methods: ["ETUDE_DE_CAS"], children: [] }] }],
    };
    vi.stubGlobal("fetch", vi.fn((url: string) => Promise.resolve(
      url.endsWith("/need") ? response(validNeed) : response(program),
    )));
    renderWithQueryClient(
      <TrainingProgramSection caseId="case-1" caseTheme="Cybersécurité" onChanged={vi.fn()} />,
    );

    expect(await screen.findByText("Informations générales du programme")).toBeInTheDocument();
    expect(screen.getByText("Le titre du programme semble différent du thème de la formation.")).toBeInTheDocument();
    expect(screen.getByText("Sélectionnez un module pour afficher et modifier son contenu.")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Menaces et risques" }));
    expect(screen.getByLabelText("Titre du module")).toHaveValue("Menaces et risques");
    expect(screen.getAllByText("1 h 30 min").length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: "Enregistrer le brouillon" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "Soumettre pour validation" })).toBeEnabled();
  });

  it("affiche une seule action de génération et un retour au besoin", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.fn((url: string) => Promise.resolve(
      url.endsWith("/need")
        ? response(validNeed)
        : response({ code: "TRAINING_PROGRAM_NOT_FOUND", message: "Introuvable" }, 404),
    ));
    vi.stubGlobal("fetch", fetchMock);
    renderWithQueryClient(
      <TrainingProgramSection caseId="case-1" caseTheme="Audit RH" onChanged={vi.fn()} />,
    );
    const generate = await screen.findByRole("button", {
      name: "Générer le programme",
    });
    expect(screen.getByRole("link", { name: "Retour au besoin" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Créer manuellement" })).not.toBeInTheDocument();
    await user.click(generate);
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });

  it("appelle une seule fois la génération après confirmation", async () => {
    const user = userEvent.setup();
    const generated = {
      id: "program-1",
      training_case_id: "case-1",
      title: "Audit RH",
      general_objectives: "Objectifs",
      prerequisites: "Aucun prérequis particulier.",
      evaluation_method: "Évaluation finale",
      is_submitted: false,
      is_validated: false,
      submitted_at: null,
      validated_at: null,
      returned_at: null,
      return_reason: null,
      expected_total_minutes: 180,
      theory_total_minutes: 90,
      practice_total_minutes: 90,
      total_minutes: 180,
      days: [],
      pedagogical_correction_performed: true,
      pedagogical_warning: (
        "Le programme a été généré mais certains éléments méritent une vérification pédagogique."
      ),
    };
    const fetchMock = vi.fn((url: string, options?: RequestInit) => Promise.resolve(
      url.endsWith("/need")
        ? response(validNeed)
        : options?.method === "POST"
          ? response(generated)
          : response({ code: "TRAINING_PROGRAM_NOT_FOUND", message: "Introuvable" }, 404),
    ));
    vi.stubGlobal("fetch", fetchMock);
    renderWithQueryClient(
      <TrainingProgramSection caseId="case-1" caseTheme="Audit RH" onChanged={vi.fn()} />,
    );
    await user.click(
      await screen.findByRole("button", { name: "Générer le programme" }),
    );
    expect(await screen.findByDisplayValue("Aucun prérequis particulier.")).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent(
      "certains éléments méritent une vérification pédagogique",
    );
    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(screen.getByRole("button", { name: "Soumettre pour validation" })).toBeEnabled();
  });

  it("bloque toute génération lorsqu’aucun besoin n’est associé", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(
      response({ code: "NOT_FOUND", message: "Introuvable" }, 404),
    ));
    renderWithQueryClient(
      <TrainingProgramSection caseId="case-1" caseTheme="Audit RH" onChanged={vi.fn()} />,
    );

    expect(await screen.findByRole("alert")).toHaveTextContent("aucun besoin client n’est associé");
    expect(screen.queryByRole("button", { name: "Générer le programme" }))
      .not.toBeInTheDocument();
  });
});
