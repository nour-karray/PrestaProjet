import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { TrainingDocumentsSection } from "@/components/training-documents-section";
import { renderWithQueryClient } from "@/tests/test-utils";

const documents = [
  ["PROGRAM", "Programme PDF"],
  ["QUOTE", "Devis"],
  ["AGREEMENT", "Convention"],
  ["ATTENDANCE_SHEET", "Feuille de présence"],
  ["CERTIFICATE", "Attestation"],
].map(([document_type, display_name], index) => ({
  id: `document-${index}`,
  training_case_id: "case-1",
  document_type,
  status: index === 0 ? "GENERATED" : index === 1 ? "FAILED" : "PENDING",
  display_name,
  original_filename: index === 0 ? "programme_TR-2026-000001.pdf" : null,
  mime_type: index === 0 ? "application/pdf" : null,
  file_size: index === 0 ? 2048 : null,
  sha256: index === 0 ? "a".repeat(64) : null,
  generation_error: index === 1 ? "La génération du PDF a échoué." : null,
  generated_at: index === 0 ? "2026-07-25T10:00:00Z" : null,
  created_at: "2026-07-25T09:00:00Z",
  updated_at: "2026-07-25T10:00:00Z",
}));

const response = (body: unknown) =>
  new Response(JSON.stringify(body), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("Documents", () => {
  it("affiche les cinq documents, badges, actions et email désactivé", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response(documents)));
    renderWithQueryClient(
      <TrainingDocumentsSection
        caseId="case-1"
        caseStatus="DOCUMENTS_A_GENERER"
        onChanged={vi.fn()}
      />,
    );

    expect(await screen.findByText("Programme PDF")).toBeInTheDocument();
    expect(screen.getByText("Devis")).toBeInTheDocument();
    expect(screen.getByText("Convention")).toBeInTheDocument();
    expect(screen.getByText("Feuille de présence")).toBeInTheDocument();
    expect(screen.getByText("Attestation")).toBeInTheDocument();
    expect(screen.getByText("Généré")).toBeInTheDocument();
    expect(screen.getByText("Échec")).toBeInTheDocument();
    expect(screen.getAllByText("En attente")).toHaveLength(3);
    expect(screen.getByRole("button", { name: "Générer tout" })).toBeEnabled();
    expect(
      screen.getByRole("button", { name: /Envoyer par email/ }),
    ).toBeDisabled();
    expect(screen.getAllByRole("button", { name: "Télécharger" })[0]).toBeEnabled();
    expect(screen.getAllByRole("button", { name: "Télécharger" })[1]).toBeDisabled();
  });

  it("lance une génération individuelle et rafraîchit le dossier", async () => {
    const user = userEvent.setup();
    const onChanged = vi.fn();
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(response(documents))
      .mockResolvedValueOnce(response({ ...documents[1], status: "GENERATED" }))
      .mockResolvedValue(response(documents));
    vi.stubGlobal("fetch", fetchMock);
    renderWithQueryClient(
      <TrainingDocumentsSection
        caseId="case-1"
        caseStatus="DOCUMENTS_A_GENERER"
        onChanged={onChanged}
      />,
    );

    await screen.findByText("Programme PDF");
    await user.click(screen.getAllByRole("button", { name: "Générer" })[0]);
    await waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining("/documents/QUOTE/generate"),
        expect.objectContaining({ method: "POST" }),
      ),
    );
    expect(onChanged).toHaveBeenCalled();
  });

  it("rend les documents immuables après clôture tout en gardant le téléchargement", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response(documents)));
    renderWithQueryClient(
      <TrainingDocumentsSection
        caseId="case-1"
        caseStatus="TERMINE"
        onChanged={vi.fn()}
      />,
    );

    await screen.findByText("Programme PDF");
    expect(screen.queryByRole("button", { name: "Générer tout" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Régénérer" })).not.toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: "Télécharger" })[0]).toBeEnabled();
  });
});
