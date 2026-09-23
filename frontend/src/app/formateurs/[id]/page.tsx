"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";

import { AppShell } from "@/components/app-shell";
import { ErrorState, LoadingState, PageHeader, StatusBadge } from "@/components/ui";
import { TrainerForm } from "@/components/trainer-form";
import { getTrainer, getTrainerCvUrl, updateTrainer } from "@/features/trainers/api";
import { ApiError } from "@/lib/api";

export default function TrainerDetailPage() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<"profile" | "cv">("profile");
  const query = useQuery({ queryKey: ["trainer", id], queryFn: () => getTrainer(id) });
  const update = useMutation({
    mutationFn: (values: Parameters<typeof updateTrainer>[1]) => updateTrainer(id, values),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["trainer", id] }),
  });

  return (
    <AppShell>
      <Link href="/formateurs" className="mb-3 inline-block text-sm font-semibold text-[var(--violet)]">← Retour</Link>
      <PageHeader eyebrow="Profil formateur" title={query.data?.full_name || "Fiche formateur"} description="Informations professionnelles et coordonnées du formateur." action={query.data && <StatusBadge tone={query.data.is_active ? "success" : "neutral"}>{query.data.is_active ? "Actif" : "Archivé"}</StatusBadge>} />
      {query.isPending && <LoadingState label="Chargement du formateur…" />}
      {query.isError && <ErrorState label="Impossible de charger le formateur." />}
      {query.data && (
        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex gap-6 border-b text-sm font-semibold" role="tablist" aria-label="Informations du formateur">
            <button type="button" role="tab" aria-selected={tab === "profile"} className={tab === "profile" ? "border-b-2 border-violet-600 pb-3 text-violet-700" : "pb-3 text-slate-500"} onClick={() => setTab("profile")}>Profil extrait</button>
            <button type="button" role="tab" aria-selected={tab === "cv"} className={tab === "cv" ? "border-b-2 border-violet-600 pb-3 text-violet-700" : "pb-3 text-slate-500"} onClick={() => setTab("cv")}>CV original</button>
          </div>
          {tab === "profile" ? <div className="pt-5"><TrainerForm initial={query.data} pending={update.isPending} submitLabel="Enregistrer les modifications" onSubmit={(values) => update.mutate(values)} />
            {update.isSuccess && <p role="status" className="toast-success mt-4">Modifications enregistrées.</p>}
            {update.error && <p role="alert" className="mt-4 text-sm text-red-700">{update.error instanceof ApiError ? update.error.message : "La modification a échoué."}</p>}
          </div> : <div className="pt-5">
            {query.data.cv_id ? <><p className="mb-4 text-sm text-slate-600">Consultez le document d’origine utilisé pour créer ce profil.</p><a href={getTrainerCvUrl(query.data.id)} target="_blank" rel="noreferrer" className="btn btn-secondary">Ouvrir le CV original</a><iframe className="mt-5 h-[620px] w-full rounded-xl border border-slate-200" title={`CV original de ${query.data.full_name}`} src={getTrainerCvUrl(query.data.id)} /></> : <p className="py-8 text-sm text-slate-500">Aucun CV original n’est associé à ce formateur.</p>}
          </div>}
        </section>
      )}
    </AppShell>
  );
}
