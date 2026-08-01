"use client";

import { useState } from "react";

import type { TrainerInput } from "@/types/trainer";

const fields: {
  name: keyof TrainerInput;
  label: string;
  type?: "number" | "email" | "url";
}[] = [
  { name: "full_name", label: "Nom et prénom" },
  { name: "birth_date", label: "Date de naissance" },
  { name: "birth_place", label: "Lieu de naissance" },
  { name: "email", label: "Mail", type: "email" },
  { name: "address", label: "Adresse" },
  { name: "company", label: "Employeur actuel" },
  { name: "employer_address", label: "Adresse de l’employeur" },
  { name: "phone", label: "Téléphone" },
  { name: "mobile_phone", label: "GSM" },
];

export function TrainerForm({
  initial,
  pending,
  submitLabel,
  onSubmit,
}: {
  initial?: Partial<TrainerInput>;
  pending: boolean;
  submitLabel: string;
  onSubmit: (input: TrainerInput) => void;
}) {
  const [values, setValues] = useState<TrainerInput>({ full_name: "", ...initial });

  function update(name: keyof TrainerInput, value: string) {
    if (name === "years_experience" || name === "daily_rate" || name === "hourly_rate") {
      setValues((current) => ({ ...current, [name]: value === "" ? null : Number(value) }));
      return;
    }
    setValues((current) => ({ ...current, [name]: value || null }));
  }

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit(values);
      }}
      className="grid gap-4 md:grid-cols-2"
    >
      {fields.map((field) => (
        <label key={field.name} className="grid gap-1.5 text-xs font-semibold text-slate-700">
          {field.label}{field.name === "full_name" ? " *" : ""}
          <input
            required={field.name === "full_name"}
            type={field.type ?? "text"}
            min={field.type === "number" ? 0 : undefined}
            value={String(values[field.name] ?? "")}
            onChange={(event) => update(field.name, event.target.value)}
            className="rounded-md border border-slate-300 px-3 py-2.5 font-normal"
          />
        </label>
      ))}
      <button disabled={pending} className="rounded-md bg-blue-600 px-5 py-3 font-semibold text-white disabled:opacity-60 md:col-span-2">
        {pending ? "Enregistrement…" : submitLabel}
      </button>
    </form>
  );
}
