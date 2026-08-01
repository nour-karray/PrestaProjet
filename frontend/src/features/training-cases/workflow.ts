import type { TrainingCaseStatus } from "@/types/training-case";
import type { WorkflowStep } from "@/components/ui";

export const workflowLabels = [
  "Demande",
  "Besoin",
  "Formateur",
  "Accord de principe",
  "Programme",
  "Prix",
  "Acceptation finale",
  "Documents",
] as const;

const statusStep: Record<TrainingCaseStatus, number> = {
  BROUILLON: 0,
  DEMANDE_RECUE: 1,
  BESOIN_A_COMPLETER: 1,
  BESOIN_COMPLETE: 2,
  RECHERCHE_FORMATEUR: 2,
  FORMATEUR_PROPOSE: 2,
  FORMATEUR_ACCEPTE: 3,
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

const lockReasons = [
  "",
  "Disponible après la création de la demande",
  "Disponible après la complétion du besoin",
  "Disponible après la confirmation du formateur",
  "Le programme sera disponible après l’accord du client.",
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
