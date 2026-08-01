export type TrainerInput = {
  first_name?: string | null;
  last_name?: string | null;
  full_name: string;
  email?: string | null;
  phone?: string | null;
  mobile_phone?: string | null;
  birth_date?: string | null;
  birth_place?: string | null;
  address?: string | null;
  company?: string | null;
  employer_address?: string | null;
  job_title?: string | null;
  years_experience?: number | null;
  hourly_rate?: number | null;
  daily_rate?: number | null;
  city?: string | null;
  country?: string | null;
  linkedin_url?: string | null;
  website?: string | null;
  notes?: string | null;
};

export type Trainer = TrainerInput & {
  id: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type TrainerList = {
  items: Trainer[];
  total: number;
  page: number;
  page_size: number;
};

export type CvStatus =
  | "UPLOADED"
  | "TEXT_EXTRACTED"
  | "OCR_REQUIRED"
  | "OCR_COMPLETED"
  | "AI_ANALYSIS_PENDING"
  | "AI_ANALYSIS_COMPLETED"
  | "REVIEW_REQUIRED"
  | "FAILED"
  | "VALIDATED";

export type TrainerCv = {
  id: string;
  trainer_id: string | null;
  original_filename: string;
  mime_type: string;
  file_size: number;
  sha256: string;
  uploaded_at: string;
  extraction_status: CvStatus;
  extraction_model: string | null;
  extraction_duration_ms: number | null;
  parsed_json: Partial<TrainerInput> | null;
  extraction_error: string | null;
  extraction_error_code: string | null;
};
