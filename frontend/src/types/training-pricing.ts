export const allowedVatRates = ["19.000", "13.000", "7.000", "0.000"] as const;
export type VatRate = (typeof allowedVatRates)[number];
export type TrainerCostInitializationMethod = "DAILY_RATE" | "HOURLY_RATE" | "NONE";

export type TrainingPricing = {
  id: string;
  training_case_id: string;
  currency: "TND";
  trainer_cost: string;
  transport_cost: string;
  room_cost: string;
  meal_cost: string;
  other_cost: string;
  margin_rate: string;
  margin_amount: string;
  total_costs: string;
  total_excluding_tax: string;
  vat_rate: VatRate;
  vat_amount: string;
  total_including_tax: string;
  vat_exemption_reason: string | null;
  vat_legal_reference: string | null;
  trainer_daily_rate_snapshot: string | null;
  trainer_hourly_rate_snapshot: string | null;
  program_day_count_snapshot: number;
  program_duration_minutes_snapshot: number;
  trainer_cost_initialization_method: TrainerCostInitializationMethod;
  is_submitted: boolean;
  submitted_at: string | null;
  is_validated: boolean;
  validated_at: string | null;
  returned_at: string | null;
  return_reason: string | null;
  editable: boolean;
  created_at: string;
  updated_at: string;
};

export type TrainingPricingInput = Pick<
  TrainingPricing,
  | "trainer_cost"
  | "transport_cost"
  | "room_cost"
  | "meal_cost"
  | "other_cost"
  | "margin_rate"
  | "vat_rate"
  | "vat_exemption_reason"
  | "vat_legal_reference"
>;

