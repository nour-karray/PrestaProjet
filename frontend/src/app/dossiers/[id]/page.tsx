"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";

import { AppShell } from "@/components/app-shell";
import { ErrorState, Icon, LoadingState, StatusBadge, WorkflowStepper } from "@/components/ui";
import { TrainingPricingSection } from "@/components/training-pricing-section";
import { TrainingDocumentsSection } from "@/components/training-documents-section";
import { TrainingProgramSection } from "@/components/training-program-section";
import { TrainingNeedSection } from "@/components/training-need-section";
import { TrainingCaseForm } from "@/components/training-case-form";
import { getCompanies } from "@/features/companies/api";
import {
  archiveTrainingCase,
  cancelTrainingCase,
  changeTrainingCaseStatus,
  getTrainingCase,
  getTrainingCaseActivity,
  updateTrainingCase,
} from "@/features/training-cases/api";
import { statusLabel } from "@/features/training-cases/status";
import { buildWorkflowSteps } from "@/features/training-cases/workflow";
import { ApiError } from "@/lib/api";
import type { TrainingCaseStatus } from "@/types/training-case";

export default function TrainingCaseDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [editing, setEditing] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(false);
  const queryClient = useQueryClient();
  const query = useQuery({ queryKey: ["training-case", id], queryFn: () => getTrainingCase(id) });
  const activity = useQuery({
    queryKey: ["training-case-activity", id],
    queryFn: () => getTrainingCaseActivity(id),
    enabled: historyOpen,
  });
  const companies = useQuery({ queryKey: ["companies", "case-form"], queryFn: () => getCompanies({}) });
  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ["training-case", id] });
    queryClient.invalidateQueries({ queryKey: ["training-case-activity", id] });
    queryClient.invalidateQueries({ queryKey: ["training-cases"] });
  };
  const updateMutation = useMutation({ mutationFn: (values: Parameters<typeof updateTrainingCase>[1]) => updateTrainingCase(id, values), onSuccess: () => { refresh(); setEditing(false); } });
  const statusMutation = useMutation({ mutationFn: (status: TrainingCaseStatus) => changeTrainingCaseStatus(id, status), onSuccess: refresh });
  const cancelMutation = useMutation({ mutationFn: () => cancelTrainingCase(id), onSuccess: refresh });
  const archiveMutation = useMutation({ mutationFn: () => archiveTrainingCase(id), onSuccess: refresh });

  if (query.isPending) return <AppShell><LoadingState label="Chargement du dossier…" /></AppShell>;
  if (query.isError) return <AppShell><ErrorState label={query.error instanceof ApiError ? query.error.message : "Impossible de charger le dossier."} /></AppShell>;
  const item = query.data;
  const nextStatus: TrainingCaseStatus | null =
    item.status === "BROUILLON"
      ? "DEMANDE_RECUE"
      : item.status === "DEMANDE_RECUE"
        ? "BESOIN_A_COMPLETER"
        : item.status === "BESOIN_COMPLETE"
          ? "RECHERCHE_FORMATEUR"
          : item.status === "RECHERCHE_FORMATEUR" && item.trainer
          ? "FORMATEUR_PROPOSE"
          : item.status === "FORMATEUR_PROPOSE"
            ? "FORMATEUR_ACCEPTE"
            : item.status === "FORMATEUR_ACCEPTE"
              ? "PROGRAMME_EN_PREPARATION"
              : null;
  const cancellable = ["BROUILLON", "DEMANDE_RECUE", "RECHERCHE_FORMATEUR"].includes(item.status);
  const archivable = ["ANNULE", "TERMINE"].includes(item.status);
  const actionError = statusMutation.error ?? cancelMutation.error ?? archiveMutation.error;
  return (
    <AppShell>
      <p className="mb-3 text-xs font-semibold text-slate-500"><Link href="/dossiers" className="text-[var(--violet)]">Dossiers</Link><span className="mx-2">/</span>Détail</p>
      <header className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-4"><div><div className="flex flex-wrap items-center gap-3"><p className="font-mono text-2xl font-bold text-slate-900">{item.reference}</p><StatusBadge tone={item.status === "TERMINE" ? "success" : item.status === "ANNULE" ? "danger" : "info"}>{statusLabel(item.status)}</StatusBadge></div><p className="mt-2 text-sm text-slate-500">{item.company.name} · {item.theme}</p></div>{!item.is_archived && !["TERMINE", "ANNULE"].includes(item.status) && <button type="button" className="detail-edit-button" onClick={() => setEditing((value) => !value)}><Icon name="edit" />{editing ? "Fermer" : "Modifier"}</button>}</div>
        <div className="mt-5 grid gap-5 border-t border-slate-100 pt-4 text-xs md:grid-cols-2"><div className="grid grid-cols-[110px_1fr] gap-2"><span className="text-slate-500">Entreprise</span><strong>{item.company.name}</strong><span className="text-slate-500">Contact</span><strong>{item.primary_contact?.full_name ?? "Aucun contact"}</strong></div><div className="grid grid-cols-[110px_1fr] gap-2"><span className="text-slate-500">Formation</span><strong>{item.theme}</strong><span className="text-slate-500">Créé le</span><strong>{new Date(item.created_at).toLocaleDateString("fr-FR")}</strong><span className="text-slate-500">Période</span><strong>{item.desired_start_date ?? "—"} → {item.desired_end_date ?? "—"}</strong></div></div>
      </header>
      <WorkflowStepper steps={buildWorkflowSteps(item.status, item.id)} />
      {["BESOIN_COMPLETE", "RECHERCHE_FORMATEUR", "FORMATEUR_PROPOSE", "FORMATEUR_ACCEPTE"].includes(item.status) && (
        <section className="mt-6 rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h2 className="font-bold">Formateur</h2>
              <p className="mt-1 text-sm text-slate-500">{item.trainer ? `${item.trainer.full_name}${item.trainer.job_title ? ` — ${item.trainer.job_title}` : ""}` : "Aucun formateur sélectionné."}</p>
            </div>
            {!item.is_archived && <Link href={`/formateurs?case_id=${item.id}`} className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white">{item.trainer ? "Changer le formateur" : "Rechercher un formateur"}</Link>}
          </div>
        </section>
      )}
      {editing && <section className="mt-7 detail-edit-panel">
        <div className="detail-edit-heading"><div><p className="page-eyebrow">Modification</p><h2>Informations de la demande</h2></div><button type="button" className="btn btn-secondary" onClick={() => setEditing(false)}>Annuler</button></div>
        <TrainingCaseForm companies={companies.data?.items ?? []} initial={{ company_id: item.company.id, primary_contact_id: item.primary_contact?.id, theme: item.theme, description: item.description ?? "", desired_start_date: item.desired_start_date ?? "", desired_end_date: item.desired_end_date ?? "" }} pending={updateMutation.isPending} submitLabel="Enregistrer les modifications" onSubmit={(values) => updateMutation.mutate(values)} />
        {updateMutation.isError && <p role="alert" className="mt-3 text-red-700">La modification a échoué.</p>}
      </section>}
      <section className="mt-7">
        <div className="mt-5 flex flex-wrap gap-3">
          {nextStatus && <button onClick={() => statusMutation.mutate(nextStatus)} className="rounded-lg bg-blue-600 px-4 py-2 font-semibold text-white">{nextStatus === "FORMATEUR_PROPOSE" ? "Marquer le formateur comme proposé" : nextStatus === "FORMATEUR_ACCEPTE" ? "Marquer le formateur comme accepté" : nextStatus === "BESOIN_A_COMPLETER" ? "Ouvrir le besoin client" : `Passer à « ${statusLabel(nextStatus)} »`}</button>}
          {cancellable && <button onClick={() => cancelMutation.mutate()} className="rounded-lg border border-red-300 px-4 py-2 font-semibold text-red-700">Annuler le dossier</button>}
          {archivable && <button onClick={() => archiveMutation.mutate()} className="rounded-lg bg-slate-700 px-4 py-2 font-semibold text-white">Archiver le dossier</button>}
        </div>
        {actionError && <p role="alert" className="mt-3 text-red-700">{actionError instanceof ApiError ? actionError.message : "L’action a échoué."}</p>}
      </section>
      {["BESOIN_A_COMPLETER", "BESOIN_COMPLETE"].includes(item.status) && (
        <TrainingNeedSection caseId={item.id} onChanged={refresh} />
      )}
      {["BESOIN_COMPLETE", "PROGRAMME_EN_PREPARATION", "PROGRAMME_A_VALIDER", "PROGRAMME_VALIDE", "TARIFICATION_EN_PREPARATION", "TARIFICATION_A_VALIDER", "TARIFICATION_VALIDEE"].includes(item.status) && (
        <TrainingProgramSection caseId={item.id} caseTheme={item.theme} onChanged={refresh} />
      )}
      {["PROGRAMME_VALIDE", "TARIFICATION_EN_PREPARATION", "TARIFICATION_A_VALIDER", "TARIFICATION_VALIDEE"].includes(item.status) && (
        <TrainingPricingSection caseId={item.id} onChanged={refresh} />
      )}
      {["TARIFICATION_VALIDEE", "DOCUMENTS_A_GENERER", "DOCUMENTS_GENERES", "TERMINE"].includes(item.status) && (
        <TrainingDocumentsSection caseId={item.id} caseStatus={item.status} onChanged={refresh} />
      )}
      <section className="mt-6 rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-bold">Historique du dossier</h2>
            {!historyOpen && <p className="mt-1 text-sm text-slate-500">Consultez les changements et actions effectués sur ce dossier.</p>}
          </div>
          <button
            type="button"
            className="btn btn-secondary"
            aria-expanded={historyOpen}
            aria-controls="training-case-history"
            onClick={() => setHistoryOpen((value) => !value)}
          >
            {historyOpen ? "Masquer l’historique" : "Voir l’historique"}
          </button>
        </div>
        {historyOpen && <div id="training-case-history">
          {activity.isPending && <p className="mt-4">Chargement de l’historique…</p>}
          {activity.isError && <p role="alert" className="mt-4 text-red-700">Impossible de charger l’historique.</p>}
          {activity.data?.length === 0 && <p className="mt-4 text-slate-500">Aucune activité.</p>}
          <ul className="mt-4 divide-y">{activity.data?.map((entry) => <li key={entry.id} className="py-3"><span className="font-semibold">{entry.action.replaceAll("_", " ")}</span><span className="ml-3 text-sm text-slate-500">{new Date(entry.created_at).toLocaleString("fr-FR")}</span></li>)}</ul>
        </div>}
      </section>
    </AppShell>
  );
}
