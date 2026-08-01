import { apiRequest } from "@/lib/api";
import type {
  Activity,
  Dashboard,
  TrainingCase,
  TrainingCaseInput,
  TrainingCaseList,
  TrainingCaseStatus,
} from "@/types/training-case";

export type TrainingCaseFilters = {
  reference?: string;
  companyId?: string;
  theme?: string;
  status?: string;
  createdFrom?: string;
  createdTo?: string;
  includeArchived?: boolean;
  page?: number;
};

export function getTrainingCases(
  filters: TrainingCaseFilters,
): Promise<TrainingCaseList> {
  const params = new URLSearchParams();
  if (filters.reference) params.set("reference", filters.reference);
  if (filters.companyId) params.set("company_id", filters.companyId);
  if (filters.theme) params.set("theme", filters.theme);
  if (filters.status) params.set("status", filters.status);
  if (filters.createdFrom) params.set("created_from", filters.createdFrom);
  if (filters.createdTo) params.set("created_to", filters.createdTo);
  if (filters.includeArchived) params.set("include_archived", "true");
  if (filters.page) params.set("page", String(filters.page));
  return apiRequest(`/api/training-cases?${params.toString()}`);
}

export function getTrainingCase(id: string): Promise<TrainingCase> {
  return apiRequest(`/api/training-cases/${id}`);
}

export function createTrainingCase(
  input: TrainingCaseInput,
): Promise<TrainingCase> {
  return apiRequest("/api/training-cases", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function updateTrainingCase(
  id: string,
  input: TrainingCaseInput,
): Promise<TrainingCase> {
  return apiRequest(`/api/training-cases/${id}`, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}

export function changeTrainingCaseStatus(
  id: string,
  status: TrainingCaseStatus,
): Promise<TrainingCase> {
  return apiRequest(`/api/training-cases/${id}/change-status`, {
    method: "POST",
    body: JSON.stringify({ status }),
  });
}

export function cancelTrainingCase(id: string): Promise<TrainingCase> {
  return apiRequest(`/api/training-cases/${id}/cancel`, { method: "POST" });
}

export function archiveTrainingCase(id: string): Promise<TrainingCase> {
  return apiRequest(`/api/training-cases/${id}/archive`, { method: "POST" });
}

export function getTrainingCaseActivity(id: string): Promise<Activity[]> {
  return apiRequest(`/api/training-cases/${id}/activity`);
}

export function getDashboard(): Promise<Dashboard> {
  return apiRequest("/api/dashboard");
}
