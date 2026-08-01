import type { TrainingCaseStatus } from "@/types/training-case";

const labels: Record<TrainingCaseStatus, string> = {
  BROUILLON: "Brouillon",
  DEMANDE_RECUE: "Demande reçue",
  RECHERCHE_FORMATEUR: "Recherche formateur",
  FORMATEUR_PROPOSE: "Formateur proposé",
  FORMATEUR_ACCEPTE: "Formateur accepté",
  BESOIN_A_COMPLETER: "Besoin à compléter",
  BESOIN_COMPLETE: "Besoin complété",
  PROGRAMME_EN_PREPARATION: "Programme en préparation",
  PROGRAMME_A_VALIDER: "Programme à valider",
  PROGRAMME_VALIDE: "Programme validé",
  TARIFICATION_EN_PREPARATION: "Tarification en préparation",
  TARIFICATION_A_VALIDER: "Tarification à valider",
  TARIFICATION_VALIDEE: "Tarification validée",
  DOCUMENTS_A_GENERER: "Documents à générer",
  DOCUMENTS_GENERES: "Documents générés",
  TERMINE: "Terminé",
  ANNULE: "Annulé",
  ARCHIVE: "Archivé",
};

export function statusLabel(status: TrainingCaseStatus): string {
  return labels[status];
}
