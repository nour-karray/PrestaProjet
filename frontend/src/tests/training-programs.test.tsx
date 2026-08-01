import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { TrainingProgramSection } from "@/components/training-program-section";
import { renderWithQueryClient } from "@/tests/test-utils";

const program = {
  id: "program-1",
  training_case_id: "case-1",
  title: "Programme Audit RH",
  general_objectives: "Conduire un audit.",
  evaluation_method: "Cas pratique.",
  is_submitted: false,
  submitted_at: null,
  is_validated: false,
  validated_at: null,
  returned_at: null,
  return_reason: null,
  created_at: "2026-07-24T12:00:00Z",
  updated_at: "2026-07-24T12:00:00Z",
  expected_total_minutes: 180,
  theory_total_minutes: 60,
  practice_total_minutes: 120,
  total_minutes: 180,
  days: [
    {
      id: "day-1",
      title: "Audit",
      position: 1,
      theory_total_minutes: 60,
      practice_total_minutes: 120,
      total_minutes: 180,
      items: [
        {
          id: "item-1",
          item_type: "MODULE",
          parent_id: null,
          title: "Définition de l’audit",
          content: "Concepts et objectifs.",
          theory_minutes: 60,
          practice_minutes: 120,
          theory_total_minutes: 60,
          practice_total_minutes: 120,
          total_minutes: 180,
          position: 1,
          methods: ["EXPOSE", "EXERCICE_PRATIQUE"],
          children: [],
        },
      ],
    },
  ],
};

const response = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("Programme de formation", () => {
  it("propose la création quand aucun programme n’existe", async () => {
    const user = userEvent.setup();
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        response({ code: "TRAINING_PROGRAM_NOT_FOUND", message: "Introuvable" }, 404),
      )
      .mockResolvedValueOnce(response(program, 201));
    vi.stubGlobal("fetch", fetchMock);
    renderWithQueryClient(
      <TrainingProgramSection caseId="case-1" caseTheme="Audit RH" onChanged={vi.fn()} />,
    );

    await user.click(await screen.findByRole("button", { name: "Créer manuellement" }));
    expect(await screen.findByText("Structure du programme")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/api/training-cases/case-1/program"),
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("affiche les totaux et permet la modification d’un module", async () => {
    const user = userEvent.setup();
    const updated = {
      ...program,
      days: [
        {
          ...program.days[0],
          items: [{ ...program.days[0].items[0], title: "Audit interne" }],
        },
      ],
    };
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(response(program))
      .mockResolvedValueOnce(response(updated));
    vi.stubGlobal("fetch", fetchMock);
    renderWithQueryClient(
      <TrainingProgramSection caseId="case-1" caseTheme="Audit RH" onChanged={vi.fn()} />,
    );

    expect(await screen.findByText("Durée attendue")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /Définition de l’audit/ }));
    const title = screen.getByLabelText("Titre");
    await user.clear(title);
    await user.type(title, "Audit interne");
    await user.click(screen.getByRole("button", { name: "Enregistrer" }));

    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining("/items/item-1"),
        expect.objectContaining({ method: "PATCH" }),
      ),
    );
    expect(await screen.findByText(/Audit interne/)).toBeInTheDocument();
  });

  it("rend un programme soumis non modifiable et exige un motif de retour", async () => {
    const user = userEvent.setup();
    const submitted = {
      ...program,
      is_submitted: true,
      submitted_at: "2026-07-24T13:00:00Z",
    };
    const returned = {
      ...program,
      return_reason: "Ajouter un exemple.",
    };
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(response(submitted))
      .mockResolvedValueOnce(response(returned));
    vi.stubGlobal("fetch", fetchMock);
    renderWithQueryClient(
      <TrainingProgramSection caseId="case-1" caseTheme="Audit RH" onChanged={vi.fn()} />,
    );

    expect(await screen.findByText("Programme soumis pour validation.")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Ajouter une journée" })).not.toBeInTheDocument();
    const returnButton = screen.getByRole("button", { name: "Retourner en préparation" });
    expect(returnButton).toBeDisabled();
    await user.type(screen.getByLabelText("Motif du retour"), "Ajouter un exemple.");
    await user.click(returnButton);
    expect(await screen.findByText(/Motif du retour/)).toHaveTextContent(
      "Ajouter un exemple.",
    );
  });
});
