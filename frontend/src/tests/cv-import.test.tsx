import { fireEvent, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import ImportCvPage from "@/app/formateurs/import-cv/page";
import { renderWithQueryClient } from "@/tests/test-utils";

vi.mock("next/navigation", () => ({
  usePathname: () => "/formateurs/import-cv",
  useRouter: () => ({ replace: vi.fn() }),
}));

const uploadedCv = {
  id: "cv-1", trainer_id: null, original_filename: "cv.pdf",
  mime_type: "application/pdf", file_size: 1000, sha256: "a".repeat(64),
  uploaded_at: "2026-07-24T12:00:00Z", extraction_status: "UPLOADED",
  extraction_model: null, extraction_duration_ms: null, parsed_json: null,
  extraction_error: null, extraction_error_code: null,
};

afterEach(() => vi.unstubAllGlobals());

async function importCv() {
  const user = userEvent.setup();
  await user.upload(screen.getByLabelText("Choisir un CV"),
    new File(["pdf"], "cv.pdf", { type: "application/pdf" }));
  fireEvent.submit(screen.getByRole("button", { name: "Importer le CV" }).closest("form")!);
}

describe("Import et analyse du CV", () => {
  it("affiche les données seulement après analyse et impose la validation humaine", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify(uploadedCv), {
        status: 201, headers: { "Content-Type": "application/json" },
      }))
      .mockResolvedValueOnce(new Response(JSON.stringify({
        ...uploadedCv, extraction_status: "REVIEW_REQUIRED",
        extraction_model: "qwen-test", parsed_json: { full_name: "Camille Démo" },
      }), { status: 200, headers: { "Content-Type": "application/json" } }));
    vi.stubGlobal("fetch", fetchMock);
    renderWithQueryClient(<ImportCvPage />);
    await importCv();
    expect(await screen.findByDisplayValue("Camille Démo")).toBeInTheDocument();
    expect(screen.getByRole("button", {
      name: "Valider et créer le formateur",
    })).toBeInTheDocument();
  });

  it("permet réessai, saisie manuelle et changement de fichier si Ollama est indisponible", async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify(uploadedCv), {
        status: 201, headers: { "Content-Type": "application/json" },
      }))
      .mockResolvedValueOnce(new Response(JSON.stringify({
        ...uploadedCv, extraction_status: "REVIEW_REQUIRED",
        extraction_error_code: "LLM_UNAVAILABLE",
        extraction_error: "Le serveur Ollama est indisponible.",
      }), { status: 200, headers: { "Content-Type": "application/json" } }));
    vi.stubGlobal("fetch", fetchMock);
    renderWithQueryClient(<ImportCvPage />);
    await importCv();
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    expect(await screen.findByText(
      "L’analyse automatique est indisponible, mais le fichier a bien été importé.",
    )).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Réessayer l’analyse" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Continuer manuellement" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Choisir un autre fichier" })).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Continuer manuellement" }));
    expect(screen.getByRole("button", {
      name: "Valider et créer le formateur",
    })).toBeInTheDocument();
  });
});
