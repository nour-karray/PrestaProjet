export const pedagogicalMethods = [
  "EXPOSE",
  "DEMONSTRATION",
  "EXERCICE_PRATIQUE",
  "ETUDE_DE_CAS",
  "MISE_EN_SITUATION",
  "ECHANGE_COLLECTIF",
  "EVALUATION",
] as const;

export type PedagogicalMethod = (typeof pedagogicalMethods)[number];
export type ProgramItemType = "MODULE" | "SUBMODULE";

export type TrainingProgramItem = {
  id: string;
  item_type: ProgramItemType;
  parent_id: string | null;
  title: string;
  content: string | null;
  theory_minutes: number;
  practice_minutes: number;
  theory_total_minutes: number;
  practice_total_minutes: number;
  total_minutes: number;
  position: number;
  methods: PedagogicalMethod[];
  children: TrainingProgramItem[];
};

export type TrainingProgramDay = {
  id: string;
  title: string;
  position: number;
  theory_total_minutes: number;
  practice_total_minutes: number;
  total_minutes: number;
  items: TrainingProgramItem[];
};

export type TrainingProgram = {
  id: string;
  training_case_id: string;
  title: string;
  general_objectives: string | null;
  prerequisites: string | null;
  evaluation_method: string | null;
  is_submitted: boolean;
  submitted_at: string | null;
  is_validated: boolean;
  validated_at: string | null;
  returned_at: string | null;
  return_reason: string | null;
  expected_total_minutes: number;
  theory_total_minutes: number;
  practice_total_minutes: number;
  total_minutes: number;
  days: TrainingProgramDay[];
  pedagogical_warning?: string | null;
  pedagogical_correction_performed?: boolean;
};

export type ProgramMetadataInput = {
  title?: string | null;
  general_objectives?: string | null;
  prerequisites?: string | null;
  evaluation_method?: string | null;
};

export type ProgramItemInput = {
  item_type: ProgramItemType;
  parent_id?: string | null;
  title: string;
  content?: string | null;
  theory_minutes: number;
  practice_minutes: number;
  methods: PedagogicalMethod[];
};
