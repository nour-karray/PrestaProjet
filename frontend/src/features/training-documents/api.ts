import { apiRequest } from "@/lib/api";
import type {
  DocumentType,
  GenerateAllResult,
  TrainingDocument,
} from "@/types/training-document";

const apiUrl = import.meta.env.VITE_API_URL ?? "http://localhost:8080";

export const getTrainingDocuments = (caseId: string) =>
  apiRequest<TrainingDocument[]>(`/api/training-cases/${caseId}/documents`);

export const initializeTrainingDocuments = (caseId: string) =>
  apiRequest<TrainingDocument[]>(`/api/training-cases/${caseId}/documents/initialize`, {
    method: "POST",
  });

export const generateTrainingDocument = (caseId: string, type: DocumentType) =>
  apiRequest<TrainingDocument>(
    `/api/training-cases/${caseId}/documents/${type}/generate`,
    { method: "POST" },
  );

export const generateAllTrainingDocuments = (caseId: string) =>
  apiRequest<GenerateAllResult>(
    `/api/training-cases/${caseId}/documents/generate-all`,
    { method: "POST" },
  );

export async function downloadTrainingDocument(caseId: string, type: DocumentType) {
  const response = await fetch(
    `${apiUrl}/api/training-cases/${caseId}/documents/${type}/download`,
    { credentials: "include" },
  );
  if (!response.ok) throw new Error("Le téléchargement a échoué.");
  const disposition = response.headers.get("content-disposition") ?? "";
  const filename = disposition.match(/filename="?([^"]+)"?/)?.[1] ?? "document.pdf";
  const url = URL.createObjectURL(await response.blob());
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}
