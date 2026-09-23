import type { TrainingCaseStatus } from "@/types/training-case";
import type { WorkflowStep } from "@/components/ui";

export const workflowLabels = [
  "Demande",
  "Formateur",
  "Besoin",
  "Accord de principe",
  "Programme",
  "Prix",
  "Acceptation finale",
  "Documents",
] as const;

const statusStep: Record<TrainingCaseStatus, number> = {
  BROUILLON: 0,
  DEMANDE_RECUE: 1,
  RECHERCHE_FORMATEUR: 1,
  FORMATEUR_PROPOSE: 1,
  FORMATEUR_ACCEPTE: 2,
  BESOIN_A_COMPLETER: 2,
  BESOIN_COMPLETE: 3,
  PROGRAMME_EN_PREPARATION: 4,
  PROGRAMME_A_VALIDER: 4,
  PROGRAMME_VALIDE: 5,
  TARIFICATION_EN_PREPARATION: 5,
  TARIFICATION_A_VALIDER: 5,
  TARIFICATION_VALIDEE: 6,
  DOCUMENTS_A_GENERER: 7,
  DOCUMENTS_GENERES: 7,
  TERMINE: 7,
  ANNULE: 0,
  ARCHIVE: 7,
};

const nextStatus: Partial<Record<TrainingCaseStatus, TrainingCaseStatus>> = {
  BROUILLON: "DEMANDE_RECUE",
  DEMANDE_RECUE: "RECHERCHE_FORMATEUR",
  RECHERCHE_FORMATEUR: "FORMATEUR_PROPOSE",
  FORMATEUR_PROPOSE: "FORMATEUR_ACCEPTE",
  FORMATEUR_ACCEPTE: "BESOIN_A_COMPLETER",
  BESOIN_COMPLETE: "PROGRAMME_EN_PREPARATION",
};

export function getNextTrainingCaseStatus(
  status: TrainingCaseStatus,
  hasTrainer: boolean,
): TrainingCaseStatus | null {
  if (status === "RECHERCHE_FORMATEUR" && !hasTrainer) return null;
  return nextStatus[status] ?? null;
}

const lockReasons = [
  "",
  "Disponible après la création de la demande",
  "Disponible après la confirmation du formateur",
  "Disponible après la validation du besoin",
  "Le programme sera disponible après validation du besoin et accord de principe.",
  "Le prix sera disponible après validation du programme.",
  "Disponible après validation du prix",
  "Les documents seront disponibles après acceptation finale.",
];

export function buildWorkflowSteps(status: TrainingCaseStatus, caseId: string): WorkflowStep[] {
  const current = statusStep[status];
  return workflowLabels.map((label, index) => ({
    label,
    state: index < current ? "completed" : index === current ? "current" : "locked",
    reason: index > current ? lockReasons[index] : undefined,
    href: index <= current ? `/dossiers/${caseId}?step=${index + 1}` : undefined,
  }));
}
