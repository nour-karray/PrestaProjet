"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useParams } from "next/navigation";

import { AppShell } from "@/components/app-shell";
import { ErrorState, LoadingState, PageHeader, StatusBadge } from "@/components/ui";
import { TrainerForm } from "@/components/trainer-form";
import { getTrainer, updateTrainer } from "@/features/trainers/api";
import { ApiError } from "@/lib/api";

export default function TrainerDetailPage() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const query = useQuery({ queryKey: ["trainer", id], queryFn: () => getTrainer(id) });
  const update = useMutation({
    mutationFn: (values: Parameters<typeof updateTrainer>[1]) => updateTrainer(id, values),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["trainer", id] }),
  });

  return (
    <AppShell>
      <Link href="/formateurs" className="mb-3 inline-block text-sm font-semibold text-[var(--violet)]">← Retour aux formateurs</Link>
      <PageHeader eyebrow="Profil formateur" title={query.data?.full_name || "Fiche formateur"} description="Informations professionnelles et coordonnées du formateur." action={query.data && <StatusBadge tone={query.data.is_active ? "success" : "neutral"}>{query.data.is_active ? "Actif" : "Archivé"}</StatusBadge>} />
      {query.isPending && <LoadingState label="Chargement du formateur…" />}
      {query.isError && <ErrorState label="Impossible de charger le formateur." />}
      {query.data && (
        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <TrainerForm initial={query.data} pending={update.isPending} submitLabel="Enregistrer les modifications" onSubmit={(values) => update.mutate(values)} />
          {update.isSuccess && <p role="status" className="mt-4 text-sm text-green-700">Modifications enregistrées.</p>}
          {update.error && <p role="alert" className="mt-4 text-sm text-red-700">{update.error instanceof ApiError ? update.error.message : "La modification a échoué."}</p>}
        </section>
      )}
    </AppShell>
  );
}
