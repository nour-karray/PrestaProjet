import { apiRequest } from "@/lib/api";
import type { TrainingPricing, TrainingPricingInput } from "@/types/training-pricing";

const path = (caseId: string) => `/api/training-cases/${caseId}/pricing`;

export const getTrainingPricing = (caseId: string): Promise<TrainingPricing> =>
  apiRequest(path(caseId));

export const createTrainingPricing = (caseId: string): Promise<TrainingPricing> =>
  apiRequest(path(caseId), { method: "POST", body: "{}" });

export const updateTrainingPricing = (
  caseId: string,
  input: TrainingPricingInput,
): Promise<TrainingPricing> =>
  apiRequest(path(caseId), { method: "PATCH", body: JSON.stringify(input) });

export const submitTrainingPricing = (caseId: string): Promise<TrainingPricing> =>
  apiRequest(`${path(caseId)}/submit`, { method: "POST" });

export const returnTrainingPricing = (
  caseId: string,
  reason: string,
): Promise<TrainingPricing> =>
  apiRequest(`${path(caseId)}/return`, {
    method: "POST",
    body: JSON.stringify({ reason }),
  });

export const validateTrainingPricing = (caseId: string): Promise<TrainingPricing> =>
  apiRequest(`${path(caseId)}/validate`, { method: "POST" });

