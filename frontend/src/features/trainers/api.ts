import { apiRequest } from "@/lib/api";
import type { Trainer, TrainerCv, TrainerCvList, TrainerInput, TrainerList } from "@/types/trainer";
import type { TrainingCase } from "@/types/training-case";

export function getTrainers(search = "", includeInactive = false, specialty = ""): Promise<TrainerList> {
  const params = new URLSearchParams();
  if (search) params.set("search", search);
  if (includeInactive) params.set("include_inactive", "true");
  if (specialty) params.set("specialty", specialty);
  return apiRequest(`/api/trainers?${params.toString()}`);
}

export function getTrainer(id: string): Promise<Trainer> {
  return apiRequest(`/api/trainers/${id}`);
}

export function getTrainerCvUrl(id: string): string {
  const baseUrl = import.meta.env.VITE_API_URL ?? "http://localhost:8080";
  return `${baseUrl}/api/trainers/${id}/cv`;
}

export function createTrainer(input: TrainerInput): Promise<Trainer> {
  return apiRequest("/api/trainers", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function updateTrainer(id: string, input: Partial<TrainerInput>): Promise<Trainer> {
  return apiRequest(`/api/trainers/${id}`, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}

export function archiveTrainer(id: string): Promise<Trainer> {
  return apiRequest(`/api/trainers/${id}`, { method: "DELETE" });
}

export function uploadTrainerCv(file: File): Promise<TrainerCv> {
  const body = new FormData();
  body.append("file", file);
  return apiRequest("/api/trainer-cvs/upload", { method: "POST", body });
}

export function extractTrainerCv(id: string): Promise<TrainerCv> {
  return apiRequest(`/api/trainer-cvs/${id}/extract`, { method: "POST" });
}

export function getTrainerCv(id: string): Promise<TrainerCv> {
  // This endpoint is polled while Ollama analyses a CV. Never reuse a cached
  // UPLOADED/AI_ANALYSIS_PENDING response after the durable state has changed.
  return apiRequest(`/api/trainer-cvs/${id}`, { cache: "no-store" });
}

export function getTrainerCvs(): Promise<TrainerCvList> {
  return apiRequest("/api/trainer-cvs?page=1&page_size=20", { cache: "no-store" });
}

export function validateTrainerCv(id: string, input: TrainerInput): Promise<Trainer> {
  return apiRequest(`/api/trainer-cvs/${id}/validate`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function assignTrainer(caseId: string, trainerId: string | null): Promise<TrainingCase> {
  return apiRequest(`/api/training-cases/${caseId}/trainer`, {
    method: "POST",
    body: JSON.stringify({ trainer_id: trainerId }),
  });
}
