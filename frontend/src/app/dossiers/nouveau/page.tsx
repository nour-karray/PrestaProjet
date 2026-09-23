"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { AppShell } from "@/components/app-shell";
import { FormPageLayout, PageContainer } from "@/components/templates";
import { PageHeader, WorkflowStepper } from "@/components/ui";
import { TrainingCaseForm } from "@/components/training-case-form";
import { getCompanies } from "@/features/companies/api";
import { changeTrainingCaseStatus, createTrainingCase } from "@/features/training-cases/api";
import { workflowLabels } from "@/features/training-cases/workflow";
import { ApiError } from "@/lib/api";
import type { TrainingCase } from "@/types/training-case";

export default function NewTrainingCasePage() {
  const router = useRouter();
  const [createdCase, setCreatedCase] = useState<TrainingCase | null>(null);
  const companies = useQuery({ queryKey: ["companies", "case-form"], queryFn: () => getCompanies({}) });
  const mutation = useMutation({
    mutationFn: async ({ values, mode }: { values: Parameters<typeof createTrainingCase>[0]; mode: "continue" | "draft" }) => {
      const trainingCase = await createTrainingCase(values);
      if (mode === "draft") return trainingCase;
      await changeTrainingCaseStatus(trainingCase.id, "DEMANDE_RECUE");
      return changeTrainingCaseStatus(trainingCase.id, "RECHERCHE_FORMATEUR");
    },
    onSuccess: (trainingCase, variables) => {
      if (variables.mode === "continue") setCreatedCase(trainingCase);
      else router.push(`/dossiers/${trainingCase.id}`);
    },
  });
  return <AppShell><PageContainer><FormPageLayout>
    <p className="case-breadcrumb">Centre de formation <span>›</span> Dossiers <span>›</span> <strong>Créer un dossier</strong></p>
    <div className="case-create-heading">
      <PageHeader title="Créer un dossier de formation" description="Renseignez les informations essentielles pour démarrer le dossier." />
      <aside><span>💡</span><p><strong>Étape 1 :</strong> créez le dossier de base,<br /> puis continuez pour préciser le besoin.</p></aside>
    </div>
    <WorkflowStepper steps={workflowLabels.map((label, index) => ({ label, state: index === 0 ? "current" as const : "locked" as const, reason: index > 0 ? "Disponible après la création de la demande" : undefined }))} />
    {mutation.isError && <p role="alert" className="mb-4 text-red-700">{mutation.error instanceof ApiError ? mutation.error.message : "La création a échoué."}</p>}
    <div className="mx-auto max-w-none"><TrainingCaseForm companies={companies.data?.items ?? []} pending={mutation.isPending} onSubmit={(values, mode = "continue") => mutation.mutate({ values, mode })} /></div>
    {createdCase && <div className="modal-backdrop success-modal-backdrop"><section className="creation-success-modal" role="dialog" aria-modal="true" aria-labelledby="creation-success-title"><span>✓</span><h2 id="creation-success-title">Dossier créé avec succès</h2><p>Le dossier <strong>{createdCase.reference}</strong> a été enregistré.</p><small>Choisissez la prochaine action pour continuer.</small><div><button className="btn btn-primary" onClick={() => router.push(`/formateurs?case_id=${createdCase.id}&created=1`)}>Choisir un formateur maintenant</button><Link className="btn btn-secondary" href="/dossiers">Retour aux dossiers</Link></div></section></div>}
  </FormPageLayout></PageContainer></AppShell>;
}
