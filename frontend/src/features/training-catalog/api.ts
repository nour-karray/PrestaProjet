import { apiRequest } from "@/lib/api";

export type TrainingCatalogItem = {
  id: string;
  category: string;
  title: string;
  is_active: boolean;
};

export function getTrainingCatalog(): Promise<TrainingCatalogItem[]> {
  return apiRequest("/api/training-catalog");
}
