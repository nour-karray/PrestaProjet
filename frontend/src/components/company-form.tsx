import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";

import type { CompanyInput } from "@/types/company";

const schema = z.object({
  name: z.string().trim().min(1, "Le nom est obligatoire."),
  address: z.string(),
  city: z.string(),
  postal_code: z.string(),
  country: z.string(),
  tax_identifier: z.string(),
  website: z.string(),
  notes: z.string(),
});

type FormValues = z.infer<typeof schema>;

const fields: { name: keyof FormValues; label: string }[] = [
  { name: "name", label: "Nom" },
  { name: "address", label: "Adresse" },
  { name: "city", label: "Ville" },
  { name: "postal_code", label: "Code postal" },
  { name: "country", label: "Pays" },
  { name: "tax_identifier", label: "Identifiant fiscal" },
  { name: "website", label: "Site web" },
];

export function CompanyForm({
  initial,
  submitLabel,
  pending,
  onSubmit,
}: {
  initial?: Partial<CompanyInput>;
  submitLabel: string;
  pending: boolean;
  onSubmit: (values: CompanyInput) => void;
}) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: initial?.name ?? "",
      address: initial?.address ?? "",
      city: initial?.city ?? "",
      postal_code: initial?.postal_code ?? "",
      country: initial?.country ?? "",
      tax_identifier: initial?.tax_identifier ?? "",
      website: initial?.website ?? "",
      notes: initial?.notes ?? "",
    },
  });

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      className="grid gap-5 rounded-xl border border-slate-200 bg-white p-6 shadow-sm md:grid-cols-2"
    >
      {fields.map((field) => (
        <label key={field.name} className="grid gap-2 font-semibold">
          {field.label}
          <input
            {...register(field.name)}
            aria-label={field.label}
            className="rounded-lg border border-slate-300 px-3 py-2 font-normal"
          />
          {errors[field.name] && (
            <span className="text-sm text-red-600">{errors[field.name]?.message}</span>
          )}
        </label>
      ))}
      <label className="grid gap-2 font-semibold md:col-span-2">
        Notes
        <textarea
          {...register("notes")}
          rows={4}
          className="rounded-lg border border-slate-300 px-3 py-2 font-normal"
        />
      </label>
      <button
        disabled={pending}
        className="rounded-lg bg-blue-600 px-5 py-3 font-semibold text-white md:col-span-2"
      >
        {pending ? "Enregistrement…" : submitLabel}
      </button>
    </form>
  );
}
