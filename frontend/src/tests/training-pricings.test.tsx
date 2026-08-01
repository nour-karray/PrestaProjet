import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { TrainingPricingSection } from "@/components/training-pricing-section";
import { renderWithQueryClient } from "@/tests/test-utils";

const pricing = {
  id: "pricing-1",
  training_case_id: "case-1",
  currency: "TND",
  trainer_cost: "1200.000",
  transport_cost: "200.000",
  room_cost: "300.000",
  meal_cost: "150.000",
  other_cost: "100.000",
  margin_rate: "20.000",
  margin_amount: "390.000",
  total_costs: "1950.000",
  total_excluding_tax: "2340.000",
  vat_rate: "19.000",
  vat_amount: "444.600",
  total_including_tax: "2784.600",
  vat_exemption_reason: null,
  vat_legal_reference: null,
  trainer_daily_rate_snapshot: "400.000",
  trainer_hourly_rate_snapshot: "50.000",
  program_day_count_snapshot: 3,
  program_duration_minutes_snapshot: 1260,
  trainer_cost_initialization_method: "DAILY_RATE",
  is_submitted: false,
  submitted_at: null,
  is_validated: false,
  validated_at: null,
  returned_at: null,
  return_reason: null,
  editable: true,
  created_at: "2026-07-25T10:00:00Z",
  updated_at: "2026-07-25T10:00:00Z",
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

describe("Tarification", () => {
  it("propose la création puis affiche les deux cartes", async () => {
    const user = userEvent.setup();
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        response({ code: "TRAINING_PRICING_NOT_FOUND", message: "Introuvable" }, 404),
      )
      .mockResolvedValueOnce(response(pricing, 201));
    vi.stubGlobal("fetch", fetchMock);
    renderWithQueryClient(
      <TrainingPricingSection caseId="case-1" onChanged={vi.fn()} />,
    );

    await user.click(await screen.findByRole("button", { name: "Créer la tarification" }));
    expect(await screen.findByText("Détails des coûts")).toBeInTheDocument();
    expect(screen.getByText("Calcul du prix")).toBeInTheDocument();
    expect(screen.getByText(/Tarif journalier/)).toBeInTheDocument();
  });

  it("calcule immédiatement les montants corrigés à trois décimales", async () => {
    const user = userEvent.setup();
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response(pricing)));
    renderWithQueryClient(
      <TrainingPricingSection caseId="case-1" onChanged={vi.fn()} />,
    );

    expect(await screen.findByDisplayValue("1200.000")).toBeInTheDocument();
    expect(screen.getByText("390,000 TND")).toBeInTheDocument();
    expect(screen.getByText(/2.340,000 TND/)).toBeInTheDocument();
    expect(screen.getByText(/2.784,600 TND/)).toBeInTheDocument();

    const transport = screen.getByLabelText("Transport");
    await user.clear(transport);
    await user.type(transport, "250.000");
    expect(screen.getByText(/2.000,000 TND/)).toBeInTheDocument();
    expect(screen.getByText("400,000 TND")).toBeInTheDocument();
  });

  it("autorise les taux fiscaux prévus et exige une justification à zéro", async () => {
    const user = userEvent.setup();
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response(pricing)));
    renderWithQueryClient(
      <TrainingPricingSection caseId="case-1" onChanged={vi.fn()} />,
    );

    const vat = await screen.findByLabelText("Taux de TVA");
    await user.selectOptions(vat, "0.000");
    expect(
      screen.getByText("Saisissez un motif d’exonération ou une référence fiscale."),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Enregistrer" })).toBeDisabled();
    await user.type(screen.getByLabelText("Motif d’exonération"), "Exonération vérifiée");
    expect(screen.getByRole("button", { name: "Enregistrer" })).toBeEnabled();
    expect(screen.getByText("0,000 TND")).toBeInTheDocument();
    expect(screen.getByText(/ne fournit aucun conseil fiscal/)).toBeInTheDocument();
  });

  it("verrouille la soumission, permet le retour puis la validation", async () => {
    const user = userEvent.setup();
    const submitted = {
      ...pricing,
      is_submitted: true,
      editable: false,
      submitted_at: "2026-07-25T11:00:00Z",
    };
    const returned = {
      ...pricing,
      return_reason: "Vérifier les frais.",
    };
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(response(submitted))
      .mockResolvedValueOnce(response(returned));
    vi.stubGlobal("fetch", fetchMock);
    renderWithQueryClient(
      <TrainingPricingSection caseId="case-1" onChanged={vi.fn()} />,
    );

    expect(await screen.findByText("En attente de validation")).toBeInTheDocument();
    expect(screen.getByLabelText("Coût formateur")).toBeDisabled();
    const returnButton = screen.getByRole("button", { name: "Renvoyer en préparation" });
    expect(returnButton).toBeDisabled();
    await user.type(screen.getByLabelText("Motif du retour"), "Vérifier les frais.");
    await user.click(returnButton);
    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining("/pricing/return"),
        expect.objectContaining({ method: "POST" }),
      ),
    );
    expect(await screen.findByText(/Motif du retour/)).toHaveTextContent(
      "Vérifier les frais.",
    );
  });
});
