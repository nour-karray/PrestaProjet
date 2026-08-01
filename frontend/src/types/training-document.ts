export const documentTypes = [
  "PROGRAM",
  "QUOTE",
  "AGREEMENT",
  "ATTENDANCE_SHEET",
  "CERTIFICATE",
] as const;

export type DocumentType = (typeof documentTypes)[number];
export type DocumentStatus = "PENDING" | "GENERATED" | "FAILED";

export type TrainingDocument = {
  id: string;
  training_case_id: string;
  document_type: DocumentType;
  status: DocumentStatus;
  display_name: string;
  original_filename: string | null;
  mime_type: string | null;
  file_size: number | null;
  sha256: string | null;
  generation_error: string | null;
  generated_at: string | null;
  created_at: string;
  updated_at: string;
};

export type GenerateAllResult = {
  results: {
    document_type: DocumentType;
    success: boolean;
    document: TrainingDocument;
    error: string | null;
  }[];
  all_generated: boolean;
};
