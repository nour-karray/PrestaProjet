import { apiRequest } from "@/lib/api";
import type {
  ProgramItemInput,
  ProgramMetadataInput,
  TrainingProgram,
} from "@/types/training-program";

const path = (caseId: string) => `/api/training-cases/${caseId}/program`;

export const getTrainingProgram = (caseId: string): Promise<TrainingProgram> =>
  apiRequest(path(caseId));

export const createTrainingProgram = (
  caseId: string,
  input: ProgramMetadataInput,
): Promise<TrainingProgram> =>
  apiRequest(path(caseId), { method: "POST", body: JSON.stringify(input) });

export const generateTrainingProgramDraft = (caseId: string): Promise<TrainingProgram> =>
  apiRequest(`${path(caseId)}/generate-draft`, { method: "POST" });

export const updateTrainingProgram = (
  caseId: string,
  input: ProgramMetadataInput,
): Promise<TrainingProgram> =>
  apiRequest(path(caseId), { method: "PATCH", body: JSON.stringify(input) });

export const addProgramDay = (caseId: string, title?: string): Promise<TrainingProgram> =>
  apiRequest(`${path(caseId)}/days`, {
    method: "POST",
    body: JSON.stringify({ title: title || null }),
  });

export const updateProgramDay = (
  caseId: string,
  dayId: string,
  title: string,
): Promise<TrainingProgram> =>
  apiRequest(`${path(caseId)}/days/${dayId}`, {
    method: "PATCH",
    body: JSON.stringify({ title }),
  });

export const deleteProgramDay = (
  caseId: string,
  dayId: string,
): Promise<TrainingProgram> =>
  apiRequest(`${path(caseId)}/days/${dayId}`, { method: "DELETE" });

export const moveProgramDay = (
  caseId: string,
  dayId: string,
  direction: "up" | "down",
): Promise<TrainingProgram> =>
  apiRequest(`${path(caseId)}/days/${dayId}/move-${direction}`, { method: "POST" });

export const addProgramItem = (
  caseId: string,
  dayId: string,
  input: ProgramItemInput,
): Promise<TrainingProgram> =>
  apiRequest(`${path(caseId)}/days/${dayId}/items`, {
    method: "POST",
    body: JSON.stringify(input),
  });

export const updateProgramItem = (
  caseId: string,
  itemId: string,
  input: Partial<Omit<ProgramItemInput, "item_type" | "parent_id">>,
): Promise<TrainingProgram> =>
  apiRequest(`${path(caseId)}/items/${itemId}`, {
    method: "PATCH",
    body: JSON.stringify(input),
  });

export const deleteProgramItem = (
  caseId: string,
  itemId: string,
): Promise<TrainingProgram> =>
  apiRequest(`${path(caseId)}/items/${itemId}`, { method: "DELETE" });

export const moveProgramItem = (
  caseId: string,
  itemId: string,
  direction: "up" | "down",
): Promise<TrainingProgram> =>
  apiRequest(`${path(caseId)}/items/${itemId}/move-${direction}`, { method: "POST" });

export const submitTrainingProgram = (caseId: string): Promise<TrainingProgram> =>
  apiRequest(`${path(caseId)}/submit`, { method: "POST" });

export const returnTrainingProgram = (
  caseId: string,
  reason: string,
): Promise<TrainingProgram> =>
  apiRequest(`${path(caseId)}/return`, {
    method: "POST",
    body: JSON.stringify({ reason }),
  });

export const validateTrainingProgram = (caseId: string): Promise<TrainingProgram> =>
  apiRequest(`${path(caseId)}/validate`, { method: "POST" });
