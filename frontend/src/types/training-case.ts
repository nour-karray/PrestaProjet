import type { Contact } from "@/types/company";

export const trainingCaseStatuses = [
  "BROUILLON",
  "DEMANDE_RECUE",
  "RECHERCHE_FORMATEUR",
  "FORMATEUR_PROPOSE",
  "FORMATEUR_ACCEPTE",
  "BESOIN_A_COMPLETER",
  "BESOIN_COMPLETE",
  "PROGRAMME_EN_PREPARATION",
  "PROGRAMME_A_VALIDER",
  "PROGRAMME_VALIDE",
  "TARIFICATION_EN_PREPARATION",
  "TARIFICATION_A_VALIDER",
  "TARIFICATION_VALIDEE",
  "DOCUMENTS_A_GENERER",
  "DOCUMENTS_GENERES",
  "TERMINE",
  "ANNULE",
  "ARCHIVE",
] as const;

export type TrainingCaseStatus = (typeof trainingCaseStatuses)[number];

export type TrainingCase = {
  id: string;
  reference: string;
  company: { id: string; name: string };
  primary_contact: Contact | null;
  trainer: { id: string; full_name: string; job_title: string | null } | null;
  theme: string;
  description: string | null;
  status: TrainingCaseStatus;
  desired_start_date: string | null;
  desired_end_date: string | null;
  created_at: string;
  updated_at: string;
  closed_at: string | null;
  is_archived: boolean;
};

export type TrainingCaseInput = {
  company_id: string;
  primary_contact_id?: string | null;
  theme: string;
  description?: string;
  desired_start_date?: string;
  desired_end_date?: string;
};

export type TrainingCaseList = {
  items: TrainingCase[];
  total: number;
  page: number;
  page_size: number;
};

export type Activity = {
  id: string;
  action: string;
  details: Record<string, unknown>;
  created_at: string;
};

export type Dashboard = {
  active_count: number;
  cancelled_count: number;
  archived_count: number;
  recent_cases: TrainingCase[];
};
