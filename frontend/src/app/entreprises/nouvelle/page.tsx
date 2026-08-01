"use client";

import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";

import { AppShell } from "@/components/app-shell";
import { PageHeader } from "@/components/ui";
import { CompanyForm } from "@/components/company-form";
import { createCompany } from "@/features/companies/api";
import { ApiError } from "@/lib/api";

export default function NewCompanyPage() {
  const router = useRouter();
  const mutation = useMutation({
    mutationFn: createCompany,
    onSuccess: (company) => router.push(`/entreprises/${company.id}`),
  });

  return (
    <AppShell>
      <PageHeader eyebrow="Répertoire clients" title="Nouvelle entreprise" description="Enregistrez les informations utiles du client. Les contacts pourront être ajoutés ensuite." />
      {mutation.isError && <p role="alert" className="mb-4 text-red-700">{mutation.error instanceof ApiError ? mutation.error.message : "La création a échoué."}</p>}
      <CompanyForm submitLabel="Créer l’entreprise" pending={mutation.isPending} onSubmit={(values) => mutation.mutate(values)} />
    </AppShell>
  );
}
