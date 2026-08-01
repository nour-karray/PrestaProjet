import { apiRequest } from "@/lib/api";
import type { TrainingNeed, TrainingNeedInput } from "@/types/training-need";

export function getTrainingNeed(caseId: string): Promise<TrainingNeed> {
  return apiRequest(`/api/training-cases/${caseId}/need`);
}

export function createTrainingNeed(caseId: string, input: TrainingNeedInput): Promise<TrainingNeed> {
  return apiRequest(`/api/training-cases/${caseId}/need`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function updateTrainingNeed(caseId: string, input: TrainingNeedInput): Promise<TrainingNeed> {
  return apiRequest(`/api/training-cases/${caseId}/need`, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}

export function validateTrainingNeed(caseId: string): Promise<TrainingNeed> {
  return apiRequest(`/api/training-cases/${caseId}/need/validate`, { method: "POST" });
}
