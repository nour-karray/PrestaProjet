"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import {
  createTrainingNeed,
  getTrainingNeed,
  updateTrainingNeed,
  validateTrainingNeed,
} from "@/features/training-needs/api";
import { ApiError } from "@/lib/api";
import { deliveryModes, type DeliveryMode, type TrainingNeedInput } from "@/types/training-need";

const emptyNeed: TrainingNeedInput = {
  target_audience: "",
  location: "",
  participant_count: null,
  delivery_mode: null,
  duration_hours: null,
  objectives: "",
  desired_start_date: "",
  desired_end_date: "",
  constraints: "",
};

const modeLabels: Record<DeliveryMode, string> = {
  PRESENTIEL: "Présentiel",
  DISTANCIEL: "Distanciel",
  HYBRIDE: "Hybride",
};

export function TrainingNeedSection({ caseId, onChanged }: { caseId: string; onChanged: () => void }) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: ["training-need", caseId],
    queryFn: () => getTrainingNeed(caseId),
    retry: false,
  });
  const [values, setValues] = useState<TrainingNeedInput>(emptyNeed);
  const [validationError, setValidationError] = useState<string | null>(null);
  const notFound = query.error instanceof ApiError && query.error.status === 404;

  useEffect(() => {
    // La réponse serveur devient la nouvelle référence après création ou sauvegarde.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (query.data) setValues({ ...emptyNeed, ...query.data });
  }, [query.data]);

  const refresh = async () => {
    await queryClient.invalidateQueries({ queryKey: ["training-need", caseId] });
    onChanged();
  };
  const save = useMutation({
    mutationFn: () =>
      query.data ? updateTrainingNeed(caseId, values) : createTrainingNeed(caseId, values),
    onSuccess: refresh,
  });
  const validation = useMutation({
    mutationFn: () => validateTrainingNeed(caseId),
    onSuccess: async () => {
      await refresh();
      router.push(`/formateurs?case_id=${caseId}`);
    },
  });

  const update = (field: keyof TrainingNeedInput, value: string) => {
    if (field === "participant_count" || field === "duration_hours") {
      setValues((current) => ({ ...current, [field]: value === "" ? null : Number(value) }));
      return;
    }
    setValues((current) => ({ ...current, [field]: value || null }));
  };

  const requestValidation = () => {
    const incomplete =
      !values.target_audience?.trim() ||
      !values.location?.trim() ||
      !values.participant_count ||
      !values.delivery_mode ||
      !values.duration_hours ||
      !values.objectives?.trim() ||
      !values.desired_start_date ||
      !values.desired_end_date;
    if (incomplete) {
      setValidationError("Renseignez tous les champs obligatoires avant la validation.");
      return;
    }
    if (values.desired_end_date! < values.desired_start_date!) {
      setValidationError("La date de fin doit suivre la date de début.");
      return;
    }
    setValidationError(null);
    if (window.confirm("Valider définitivement ce besoin client ?")) validation.mutate();
  };

  if (query.isPending) return <p role="status">Chargement du besoin client…</p>;
  if (query.isError && !notFound) {
    return <p role="alert" className="text-sm text-red-700">{query.error instanceof ApiError ? query.error.message : "Impossible de charger le besoin client."}</p>;
  }

  const readOnly = query.data?.is_validated === true;
  const actionError = save.error ?? validation.error;

  return (
    <section className="mt-6 rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="font-bold text-blue-800">Besoin du client</h2>
          <p className="mt-1 text-xs text-slate-500">
            {readOnly ? `Validé le ${new Date(query.data!.validated_at!).toLocaleString("fr-FR")}` : "Enregistrez un brouillon, puis validez-le après vérification."}
          </p>
        </div>
        <span className={`rounded px-2 py-1 text-xs font-semibold ${readOnly ? "bg-green-50 text-green-700" : "bg-amber-50 text-amber-700"}`}>{readOnly ? "Validé" : "Brouillon"}</span>
      </div>

      <fieldset disabled={readOnly || save.isPending || validation.isPending} className="mt-5 grid gap-4 md:grid-cols-2">
        <TextField label="Public cible *" value={values.target_audience} onChange={(value) => update("target_audience", value)} />
        <TextField label="Lieu *" value={values.location} onChange={(value) => update("location", value)} />
        <NumberField label="Nombre de participants *" value={values.participant_count} onChange={(value) => update("participant_count", value)} />
        <label className="grid gap-1.5 text-xs font-semibold">Modalité *
          <select aria-label="Modalité" value={values.delivery_mode ?? ""} onChange={(event) => update("delivery_mode", event.target.value)} className="rounded-md border border-slate-300 px-3 py-2.5 font-normal">
            <option value="">Sélectionner</option>
            {deliveryModes.map((mode) => <option key={mode} value={mode}>{modeLabels[mode]}</option>)}
          </select>
        </label>
        <NumberField label="Durée de la formation en heures *" value={values.duration_hours} onChange={(value) => update("duration_hours", value)} />
        <TextField label="Début souhaité *" type="date" value={values.desired_start_date} onChange={(value) => update("desired_start_date", value)} />
        <TextField label="Fin souhaitée *" type="date" value={values.desired_end_date} onChange={(value) => update("desired_end_date", value)} />
        <TextArea label="Objectifs pédagogiques *" value={values.objectives} onChange={(value) => update("objectives", value)} />
        <TextArea label="Contraintes particulières" value={values.constraints} onChange={(value) => update("constraints", value)} />
      </fieldset>

      {!readOnly && <div className="mt-5 flex flex-wrap justify-end gap-3">
        <button type="button" onClick={() => setValues(query.data ? { ...emptyNeed, ...query.data } : emptyNeed)} disabled={save.isPending || validation.isPending} className="rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold">Annuler les modifications</button>
        <button type="button" onClick={() => save.mutate()} disabled={save.isPending || validation.isPending} className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white">{save.isPending ? "Enregistrement…" : "Enregistrer le brouillon"}</button>
        {query.data && <button type="button" aria-label="Valider le besoin" onClick={requestValidation} disabled={save.isPending || validation.isPending} className="rounded-md bg-green-600 px-4 py-2 text-sm font-semibold text-white">{validation.isPending ? "Validation…" : "Enregistrer le besoin et continuer"}</button>}
      </div>}
      {validationError && <p role="alert" className="mt-4 text-sm text-red-700">{validationError}</p>}
      {actionError && <p role="alert" className="mt-4 text-sm text-red-700">{actionError instanceof ApiError ? actionError.message : "L’action a échoué."}</p>}
    </section>
  );
}

function TextField({ label, value, onChange, type = "text" }: { label: string; value: string | null | undefined; onChange: (value: string) => void; type?: "text" | "date" }) {
  return <label className="grid gap-1.5 text-xs font-semibold">{label}<input aria-label={label.replace(" *", "")} type={type} value={value ?? ""} onChange={(event) => onChange(event.target.value)} className="rounded-md border border-slate-300 px-3 py-2.5 font-normal" /></label>;
}

function NumberField({ label, value, onChange }: { label: string; value: number | null | undefined; onChange: (value: string) => void }) {
  return <label className="grid gap-1.5 text-xs font-semibold">{label}<input aria-label={label.replace(" *", "")} type="number" min="0.01" step="0.01" value={value ?? ""} onChange={(event) => onChange(event.target.value)} className="rounded-md border border-slate-300 px-3 py-2.5 font-normal" /></label>;
}

function TextArea({ label, value, onChange }: { label: string; value: string | null | undefined; onChange: (value: string) => void }) {
  return <label className="grid gap-1.5 text-xs font-semibold">{label}<textarea aria-label={label.replace(" *", "")} rows={4} value={value ?? ""} onChange={(event) => onChange(event.target.value)} className="rounded-md border border-slate-300 px-3 py-2.5 font-normal" /></label>;
}
