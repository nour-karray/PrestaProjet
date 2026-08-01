"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { EmptyState, ErrorState, LoadingState, PageHeader, PrimaryLink, StatusBadge, WorkflowActionBar, WorkflowStepper } from "@/components/ui";
import { TrainerForm } from "@/components/trainer-form";
import { createTrainer, assignTrainer, getTrainers } from "@/features/trainers/api";
import { changeTrainingCaseStatus, getTrainingCase } from "@/features/training-cases/api";
import { buildWorkflowSteps } from "@/features/training-cases/workflow";
import { ApiError } from "@/lib/api";

function TrainersContent() {
  const params = useSearchParams();
  const router = useRouter();
  const caseId = params.get("case_id");
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [manualOpen, setManualOpen] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);
  const trainers = useQuery({ queryKey: ["trainers", search], queryFn: () => getTrainers(search) });
  const trainingCase = useQuery({ queryKey: ["training-case", caseId], queryFn: () => getTrainingCase(caseId!), enabled: Boolean(caseId) });
  const selectedId = trainingCase.data?.trainer?.id ?? null;
  const createMutation = useMutation({
    mutationFn: createTrainer,
    onSuccess: () => { setManualOpen(false); queryClient.invalidateQueries({ queryKey: ["trainers"] }); },
  });
  const assignMutation = useMutation({
    mutationFn: async (trainerId: string) => {
      if (!caseId) throw new Error("Dossier manquant");
      if (trainingCase.data?.status === "BESOIN_COMPLETE") await changeTrainingCaseStatus(caseId, "RECHERCHE_FORMATEUR");
      return assignTrainer(caseId, trainerId);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["training-case", caseId] });
      setSuccess("Formateur sélectionné avec succès");
    },
  });
  const confirmMutation = useMutation({
    mutationFn: async () => {
      if (!caseId) throw new Error("Dossier manquant");
      const current = await getTrainingCase(caseId);
      if (current.status === "RECHERCHE_FORMATEUR") await changeTrainingCaseStatus(caseId, "FORMATEUR_PROPOSE");
      return changeTrainingCaseStatus(caseId, "FORMATEUR_ACCEPTE");
    },
    onSuccess: () => router.push(`/dossiers/${caseId}?step=4&trainer=confirmed`),
  });
  const error = createMutation.error ?? assignMutation.error ?? confirmMutation.error;

  return <AppShell>
    <PageHeader
      eyebrow={caseId ? "Affectation au dossier" : "Réseau de formateurs"}
      title={caseId ? "Choisir un formateur" : "Formateurs"}
      description={caseId ? "Sélectionnez un formateur existant ou importez un nouveau CV." : "Recherchez et gérez les profils de formateurs."}
      action={<div className="flex flex-wrap gap-2"><PrimaryLink href={`/formateurs/import-cv${caseId ? `?case_id=${caseId}` : ""}`}>Importer un CV</PrimaryLink><button onClick={() => setManualOpen((value) => !value)} className="btn btn-secondary">{manualOpen ? "Fermer" : caseId ? "Ajouter manuellement" : "Nouveau formateur"}</button></div>}
    />
    {trainingCase.data && <WorkflowStepper steps={buildWorkflowSteps(trainingCase.data.status, trainingCase.data.id)} />}
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      {caseId && <nav className="flex gap-8 border-b text-sm font-semibold"><span className="border-b-2 border-violet-600 px-1 pb-3 text-violet-700">Formateurs existants</span><Link href={`/formateurs/import-cv?case_id=${caseId}`} className="px-1 pb-3 text-slate-500">Importer un CV</Link></nav>}
      {success && <p className="toast-success mt-5" role="status">{success}</p>}
      {manualOpen && <div className="mt-6 rounded-lg border border-violet-100 bg-violet-50/30 p-5"><h2 className="mb-4 font-bold">Créer manuellement un formateur</h2><TrainerForm pending={createMutation.isPending} submitLabel="Créer le formateur" onSubmit={(values) => createMutation.mutate(values)} /></div>}
      <div className="mt-5 flex gap-3"><input aria-label="Rechercher un formateur" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Nom, spécialité, ville…" className="field min-w-0 flex-1" /></div>
      <h2 className="mb-2 mt-6 text-sm font-bold">Formateurs disponibles</h2>
      {trainers.isPending && <LoadingState label="Chargement des formateurs…" />}
      {trainers.isError && <ErrorState label="Impossible de charger les formateurs." />}
      {trainers.data?.items.length === 0 && <EmptyState title="Aucun formateur trouvé." description="Modifiez votre recherche ou importez un CV." />}
      <ul className="grid gap-3">
        {trainers.data?.items.map((trainer) => {
          const selected = selectedId === trainer.id;
          return <li key={trainer.id} className={`flex flex-wrap items-center gap-4 rounded-xl border border-slate-200 p-4 ${selected ? "selected-trainer" : ""}`}>
            <span className="grid size-11 place-items-center rounded-full bg-violet-100 font-bold text-violet-700">{trainer.full_name.slice(0, 1).toUpperCase()}</span>
            <div className="min-w-0 flex-1"><p className="font-bold">{trainer.full_name}</p><p className="text-xs text-slate-500">{[trainer.job_title, trainer.city].filter(Boolean).join(" · ") || "Profil à compléter"}</p></div>
            <StatusBadge tone={trainer.is_active ? "success" : "danger"}>{selected ? "✓ Sélectionné" : trainer.is_active ? "Confirmée" : "Indisponible"}</StatusBadge>
            <Link href={`/formateurs/${trainer.id}`} className="btn btn-ghost">Voir le profil</Link>
            {caseId && <button onClick={() => assignMutation.mutate(trainer.id)} disabled={!trainer.is_active || assignMutation.isPending || selected} className="btn btn-secondary">{assignMutation.isPending && assignMutation.variables === trainer.id ? "Sélection…" : selected ? "Sélectionné" : "Sélectionner"}</button>}
          </li>;
        })}
      </ul>
      {selectedId && trainingCase.data?.trainer && <aside className="mt-5 rounded-xl border border-violet-200 bg-violet-50 p-4"><strong>{trainingCase.data.trainer.full_name}</strong><p className="text-sm text-slate-600">{trainingCase.data.trainer.job_title || "Spécialités à compléter"} · Disponibilité confirmée</p><button className="mt-2 text-xs font-bold text-violet-700" onClick={() => setSuccess(null)}>Changer de formateur</button></aside>}
      {error && <p role="alert" className="mt-4 text-sm text-red-700">{error instanceof ApiError ? error.message : "L’action a échoué."}</p>}
      {caseId && <WorkflowActionBar back={<Link className="btn btn-secondary" href={`/dossiers/${caseId}?step=2`}>Retour au besoin</Link>} prerequisite={!selectedId ? "Sélectionnez un formateur disponible pour continuer." : undefined} status={selectedId ? "La sélection est enregistrée dans le dossier." : "Aucun formateur sélectionné"} primary={<button className="btn btn-primary" disabled={!selectedId || confirmMutation.isPending} onClick={() => confirmMutation.mutate()}>{confirmMutation.isPending ? "Confirmation…" : "Confirmer le formateur et continuer"}</button>} />}
    </section>
  </AppShell>;
}

export default function TrainersPage() {
  return <Suspense fallback={<LoadingState />}><TrainersContent /></Suspense>;
}
