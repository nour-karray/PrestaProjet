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

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("Génération assistée du programme", () => {
  it("affiche les deux choix et respecte l’annulation de confirmation", async () => {
    const user = userEvent.setup();
    const fetchMock = vi.fn().mockResolvedValue(
      response({ code: "TRAINING_PROGRAM_NOT_FOUND", message: "Introuvable" }, 404),
    );
    vi.stubGlobal("fetch", fetchMock);
    vi.spyOn(window, "confirm").mockReturnValue(false);
    renderWithQueryClient(
      <TrainingProgramSection caseId="case-1" caseTheme="Audit RH" onChanged={vi.fn()} />,
    );
    const generate = await screen.findByRole("button", {
      name: "Générer un brouillon avec Ollama",
    });
    expect(screen.getByRole("button", { name: "Créer manuellement" })).toBeEnabled();
    await user.click(generate);
    expect(fetchMock).toHaveBeenCalledTimes(1);
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
    };
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        response({ code: "TRAINING_PROGRAM_NOT_FOUND", message: "Introuvable" }, 404),
      )
      .mockResolvedValueOnce(response(generated));
    vi.stubGlobal("fetch", fetchMock);
    vi.spyOn(window, "confirm").mockReturnValue(true);
    renderWithQueryClient(
      <TrainingProgramSection caseId="case-1" caseTheme="Audit RH" onChanged={vi.fn()} />,
    );
    await user.click(
      await screen.findByRole("button", { name: "Générer un brouillon avec Ollama" }),
    );
    expect(await screen.findByDisplayValue("Aucun prérequis particulier.")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(screen.getByRole("button", { name: "Soumettre pour validation" })).toBeEnabled();
  });
});
