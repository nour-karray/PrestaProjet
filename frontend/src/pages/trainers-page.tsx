import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link, { useRouter, useSearchParams } from "@/router/navigation";
import { Suspense, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { TrainerCvImportFlow } from "@/pages/import-cv-page";
import { EmptyState, ErrorState, FeedbackToast, LoadingState, PageHeader, StatusBadge, WorkflowActionBar, WorkflowStepper } from "@/components/ui";
import { assignTrainer, getTrainers } from "@/features/trainers/api";
import { changeTrainingCaseStatus, getTrainingCase } from "@/features/training-cases/api";
import { buildWorkflowSteps } from "@/features/training-cases/workflow";
import { ApiError } from "@/lib/api";

function TrainersContent() {
  const params = useSearchParams();
  const router = useRouter();
  const caseId = params.get("case_id");
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [activePanel, setActivePanel] = useState<"existing" | "import">("existing");
  const [success, setSuccess] = useState<string | null>(null);
  const trainingCase = useQuery({ queryKey: ["training-case", caseId], queryFn: () => getTrainingCase(caseId!), enabled: Boolean(caseId) });
  const specialty = caseId ? trainingCase.data?.theme ?? "" : "";
  const trainers = useQuery({
    queryKey: ["trainers", search, specialty],
    queryFn: () => getTrainers(search, false, specialty),
    enabled: !caseId || Boolean(specialty),
  });
  const selectedId = trainingCase.data?.trainer?.id ?? null;
  const assignMutation = useMutation({
    mutationFn: async (trainerId: string) => {
      if (!caseId) throw new Error("Dossier manquant");
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
      if (current.status === "BESOIN_A_COMPLETER") return current;
      if (current.status === "FORMATEUR_ACCEPTE") {
        return changeTrainingCaseStatus(caseId, "BESOIN_A_COMPLETER");
      }
      if (current.status === "RECHERCHE_FORMATEUR") {
        await changeTrainingCaseStatus(caseId, "FORMATEUR_PROPOSE");
        await changeTrainingCaseStatus(caseId, "FORMATEUR_ACCEPTE");
        return changeTrainingCaseStatus(caseId, "BESOIN_A_COMPLETER");
      }
      if (current.status === "FORMATEUR_PROPOSE") {
        await changeTrainingCaseStatus(caseId, "FORMATEUR_ACCEPTE");
        return changeTrainingCaseStatus(caseId, "BESOIN_A_COMPLETER");
      }
      throw new ApiError(409, "INVALID_STATUS_TRANSITION", "Ce dossier n’attend plus la confirmation d’un formateur.");
    },
    onSuccess: (updated) => {
      queryClient.setQueryData(["training-case", caseId], updated);
      router.push(`/dossiers/${caseId}?step=3&trainer=confirmed`);
    },
  });
  const error = assignMutation.error ?? confirmMutation.error;

  return <AppShell>
    <PageHeader
      eyebrow={caseId ? "Affectation au dossier" : "Réseau de formateurs"}
      title={caseId ? "Choisir un formateur" : "Formateurs"}
      description={caseId ? "Sélectionnez un formateur existant ou importez un nouveau CV." : "Recherchez et gérez les profils de formateurs."}
    />
    {caseId && specialty && <section aria-label="Formation du dossier" className="flex items-center gap-3 rounded-xl border border-violet-200 bg-violet-50 px-4 py-3 text-sm text-slate-700">
      <span className="grid size-9 shrink-0 place-items-center rounded-lg bg-white text-violet-700 shadow-sm"><span aria-hidden="true">📘</span></span>
      <div><span className="block text-xs font-semibold uppercase tracking-wide text-violet-700">Type de formation du dossier</span><strong className="text-base text-slate-950">{specialty}</strong></div>
    </section>}
    {trainingCase.data && <WorkflowStepper steps={buildWorkflowSteps(trainingCase.data.status, trainingCase.data.id)} />}
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <nav className="flex gap-8 border-b text-sm font-semibold" role="tablist" aria-label="Mode de sélection du formateur">
        <button role="tab" aria-selected={activePanel === "existing"} className={activePanel === "existing" ? "border-b-2 border-violet-600 px-1 pb-3 text-violet-700" : "px-1 pb-3 text-slate-500"} onClick={() => setActivePanel("existing")}>Formateurs existants</button>
        <button role="tab" aria-selected={activePanel === "import"} className={activePanel === "import" ? "border-b-2 border-violet-600 px-1 pb-3 text-violet-700" : "px-1 pb-3 text-slate-500"} onClick={() => setActivePanel("import")}>Importer un CV</button>
      </nav>
      {success && <div className="mt-5"><FeedbackToast>{success}</FeedbackToast></div>}
      {activePanel === "import" && <div className="mt-5"><TrainerCvImportFlow inline caseId={caseId} onValidated={(trainer) => {
        queryClient.invalidateQueries({ queryKey: ["trainers"] });
        if (caseId) assignMutation.mutate(trainer.id);
        setActivePanel("existing");
        setSuccess(`${trainer.full_name} a été importé et sélectionné.`);
      }} /></div>}
      {activePanel === "existing" && <>
      {specialty && <p className="mt-5 text-sm text-slate-600">Spécialité recherchée : <strong className="text-slate-900">{specialty}</strong></p>}
      <div className={`${specialty ? "mt-3" : "mt-5"} flex gap-3`}><input aria-label="Rechercher un formateur" value={search} onChange={(event) => setSearch(event.target.value)} placeholder={specialty ? `Rechercher parmi les formateurs en ${specialty}…` : "Nom, spécialité, ville…"} className="field min-w-0 flex-1" /></div>
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
      {selectedId && trainingCase.data?.trainer && <aside className="mt-5 rounded-xl border border-violet-200 bg-violet-50 p-4"><strong>{trainingCase.data.trainer.full_name}</strong><p className="text-sm text-slate-600">{trainingCase.data.trainer.job_title || "Spécialités à compléter"} · Disponibilité confirmée</p><button className="mt-2 text-xs font-bold text-violet-700" onClick={() => { setSuccess("Choisissez un autre formateur dans la liste. Le statut du dossier reste inchangé."); setActivePanel("existing"); }}>Changer de formateur</button></aside>}
      {error && <div className="mt-4"><FeedbackToast tone="error">{error instanceof ApiError ? error.message : "L’action a échoué."}</FeedbackToast></div>}
      {caseId && <WorkflowActionBar back={<Link className="btn btn-secondary" href={`/dossiers/${caseId}?step=1`}>← Retour</Link>} prerequisite={!selectedId ? "Sélectionnez un formateur disponible pour continuer." : undefined} status={selectedId ? "La sélection est enregistrée dans le dossier." : "Aucun formateur sélectionné"} primary={<button className="btn btn-primary" disabled={!selectedId || confirmMutation.isPending} onClick={() => confirmMutation.mutate()}>{confirmMutation.isPending ? "Confirmation…" : "Confirmer"}</button>} />}
      </>}
    </section>
  </AppShell>;
}

export default function TrainersPage() {
  return <Suspense fallback={<LoadingState />}><TrainersContent /></Suspense>;
}
