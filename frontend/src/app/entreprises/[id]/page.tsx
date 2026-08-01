"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { useState } from "react";

import { AppShell } from "@/components/app-shell";
import { ErrorState, LoadingState, PageHeader, StatusBadge } from "@/components/ui";
import { CompanyForm } from "@/components/company-form";
import { ContactForm } from "@/components/contact-form";
import {
  createContact,
  deleteContact,
  getCompany,
  updateCompany,
  updateContact,
} from "@/features/companies/api";
import { ApiError } from "@/lib/api";
import type { Contact, ContactInput } from "@/types/company";

export default function CompanyDetailPage() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const [editingContact, setEditingContact] = useState<Contact | undefined>();
  const [showContactForm, setShowContactForm] = useState(false);
  const query = useQuery({
    queryKey: ["company", id],
    queryFn: () => getCompany(id),
  });
  const refresh = () => queryClient.invalidateQueries({ queryKey: ["company", id] });
  const companyMutation = useMutation({
    mutationFn: (values: Parameters<typeof updateCompany>[1]) => updateCompany(id, values),
    onSuccess: refresh,
  });
  const contactMutation = useMutation({
    mutationFn: (values: ContactInput) =>
      editingContact
        ? updateContact(editingContact.id, values)
        : createContact(id, values),
    onSuccess: () => {
      setShowContactForm(false);
      setEditingContact(undefined);
      refresh();
    },
  });
  const deleteMutation = useMutation({ mutationFn: deleteContact, onSuccess: refresh });
  const primaryMutation = useMutation({
    mutationFn: (contactId: string) => updateContact(contactId, { is_primary: true }),
    onSuccess: refresh,
  });

  if (query.isPending) return <AppShell><LoadingState label="Chargement de l’entreprise…" /></AppShell>;
  if (query.isError) return <AppShell><ErrorState label={query.error instanceof ApiError ? query.error.message : "Impossible de charger l’entreprise."} /></AppShell>;
  const company = query.data;

  return (
    <AppShell>
      <PageHeader eyebrow="Entreprise cliente" title={company.name} description={[company.city, company.country].filter(Boolean).join(", ") || "Informations de l’entreprise"} action={<StatusBadge tone={company.is_archived ? "neutral" : "success"}>{company.is_archived ? "Archivée" : "Active"}</StatusBadge>} />
      {companyMutation.isError && <p role="alert" className="mb-4 text-red-700">La modification a échoué.</p>}
      <CompanyForm
        initial={{
          name: company.name,
          address: company.address ?? "",
          city: company.city ?? "",
          postal_code: company.postal_code ?? "",
          country: company.country ?? "",
          tax_identifier: company.tax_identifier ?? "",
          website: company.website ?? "",
          notes: company.notes ?? "",
        }}
        submitLabel="Enregistrer les modifications"
        pending={companyMutation.isPending}
        onSubmit={(values) => companyMutation.mutate(values)}
      />

      <section className="mt-8 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold">Contacts</h2>
          <button onClick={() => { setEditingContact(undefined); setShowContactForm(true); }} className="rounded-lg bg-blue-600 px-4 py-2 font-semibold text-white">Ajouter</button>
        </div>
        {showContactForm && <div className="mt-5"><ContactForm initial={editingContact} pending={contactMutation.isPending} onSubmit={(values) => contactMutation.mutate(values)} onCancel={() => setShowContactForm(false)} /></div>}
        {contactMutation.isError && <p role="alert" className="mt-3 text-red-700">L’enregistrement du contact a échoué.</p>}
        {company.contacts.length === 0 ? (
          <p className="mt-6 text-slate-500">Aucun contact enregistré.</p>
        ) : (
          <div className="mt-5 overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead><tr>{["Nom", "Fonction", "Email", "Téléphone", "Principal", "Actions"].map((label) => <th key={label} className="border-b px-3 py-3">{label}</th>)}</tr></thead>
              <tbody>{company.contacts.map((contact) => (
                <tr key={contact.id}>
                  <td className="border-b px-3 py-3 font-semibold">{contact.full_name}</td>
                  <td className="border-b px-3 py-3">{contact.job_title ?? "—"}</td>
                  <td className="border-b px-3 py-3">{contact.email ?? "—"}</td>
                  <td className="border-b px-3 py-3">{contact.phone ?? "—"}</td>
                  <td className="border-b px-3 py-3">{contact.is_primary ? "Oui" : "Non"}</td>
                  <td className="border-b px-3 py-3"><div className="flex flex-wrap gap-2"><button className="text-blue-700" onClick={() => { setEditingContact(contact); setShowContactForm(true); }}>Modifier</button>{!contact.is_primary && <button className="text-green-700" onClick={() => primaryMutation.mutate(contact.id)}>Définir comme principal</button>}<button className="text-red-700" onClick={() => deleteMutation.mutate(contact.id)}>Supprimer</button></div></td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        )}
      </section>
    </AppShell>
  );
}
