"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";

import type { Contact, ContactInput } from "@/types/company";

const schema = z.object({
  full_name: z.string().trim().min(1, "Le nom est obligatoire."),
  email: z.union([z.literal(""), z.string().email("L’adresse email n’est pas valide.")]),
  phone: z.string(),
  job_title: z.string(),
  is_primary: z.boolean(),
});

type FormValues = z.infer<typeof schema>;

export function ContactForm({
  initial,
  pending,
  onSubmit,
  onCancel,
}: {
  initial?: Contact;
  pending: boolean;
  onSubmit: (values: ContactInput) => void;
  onCancel: () => void;
}) {
  const { register, handleSubmit, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      full_name: initial?.full_name ?? "",
      email: initial?.email ?? "",
      phone: initial?.phone ?? "",
      job_title: initial?.job_title ?? "",
      is_primary: initial?.is_primary ?? false,
    },
  });
  return (
    <form onSubmit={handleSubmit(onSubmit)} className="grid gap-4 rounded-lg bg-slate-50 p-4 md:grid-cols-2">
      <label className="grid gap-1">Nom<input {...register("full_name")} className="rounded border px-3 py-2" />{errors.full_name && <span className="text-sm text-red-600">{errors.full_name.message}</span>}</label>
      <label className="grid gap-1">Fonction<input {...register("job_title")} className="rounded border px-3 py-2" /></label>
      <label className="grid gap-1">Email<input {...register("email")} className="rounded border px-3 py-2" />{errors.email && <span className="text-sm text-red-600">{errors.email.message}</span>}</label>
      <label className="grid gap-1">Téléphone<input {...register("phone")} className="rounded border px-3 py-2" /></label>
      <label className="flex items-center gap-2"><input type="checkbox" {...register("is_primary")} />Contact principal</label>
      <div className="flex justify-end gap-3"><button type="button" onClick={onCancel} className="rounded border px-4 py-2">Annuler</button><button disabled={pending} className="rounded bg-blue-600 px-4 py-2 font-semibold text-white">Enregistrer</button></div>
    </form>
  );
}
