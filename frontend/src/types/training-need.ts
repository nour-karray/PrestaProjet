export const deliveryModes = ["PRESENTIEL", "DISTANCIEL", "HYBRIDE"] as const;

export type DeliveryMode = (typeof deliveryModes)[number];
export const trainingNeedLevels = ["BEGINNER", "INTERMEDIATE", "ADVANCED", "EXPERT"] as const;
export type TrainingNeedLevel = (typeof trainingNeedLevels)[number];

export type TrainingNeedInput = {
  target_audience?: string | null;
  level?: TrainingNeedLevel | null;
  location?: string | null;
  participant_count?: number | null;
  delivery_mode?: DeliveryMode | null;
  duration_hours?: number | null;
  planned_days_count?: number | null;
  objectives?: string | null;
  desired_start_date?: string | null;
  desired_end_date?: string | null;
  constraints?: string | null;
};

export type TrainingNeed = TrainingNeedInput & {
  id: string;
  training_case_id: string;
  is_validated: boolean;
  validated_at: string | null;
  created_at: string;
  updated_at: string;
};
