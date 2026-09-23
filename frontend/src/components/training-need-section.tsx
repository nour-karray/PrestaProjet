"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import { useRouter } from "next/navigation";

import {
  createTrainingNeed,
  getTrainingNeed,
  updateTrainingNeed,
  validateTrainingNeed,
} from "@/features/training-needs/api";
import { generateTrainingProgramDraft } from "@/features/training-programs/api";
import { ApiError } from "@/lib/api";
import { deliveryModes, trainingNeedLevels, type DeliveryMode, type TrainingNeedInput, type TrainingNeedLevel } from "@/types/training-need";

const emptyNeed: TrainingNeedInput = {
  target_audience: "",
  level: null,
  location: "",
  participant_count: null,
  delivery_mode: null,
  duration_hours: null,
  planned_days_count: null,
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

const levelLabels: Record<TrainingNeedLevel, string> = {
  BEGINNER: "Débutant",
  INTERMEDIATE: "Intermédiaire",
  ADVANCED: "Avancé",
  EXPERT: "Expert",
};

type RequiredNeedField = Exclude<keyof TrainingNeedInput, "constraints">;

const requiredFieldLabels: Record<RequiredNeedField, string> = {
  target_audience: "Public cible",
  level: "Niveau",
  location: "Lieu",
  participant_count: "Nombre de participants",
  delivery_mode: "Modalité",
  duration_hours: "Durée de la formation",
  planned_days_count: "Nombre de jours planifiés",
  objectives: "Objectifs pédagogiques",
  desired_start_date: "Début souhaité",
  desired_end_date: "Fin souhaitée",
};

function getMissingRequiredFields(values: TrainingNeedInput): RequiredNeedField[] {
  return (Object.keys(requiredFieldLabels) as RequiredNeedField[]).filter((field) => {
    const value = values[field];
    return value === null || value === undefined || value === "" ||
      (typeof value === "string" && !value.trim());
  });
}

function missingFieldsFromApi(error: unknown): RequiredNeedField[] {
  if (!(error instanceof ApiError) || error.code !== "TRAINING_NEED_INCOMPLETE") return [];
  const details = error.details;
  if (!details || typeof details !== "object" || !("missing_fields" in details)) return [];
  const fields = (details as { missing_fields?: unknown }).missing_fields;
  if (!Array.isArray(fields)) return [];
  return fields.filter(
    (field): field is RequiredNeedField =>
      typeof field === "string" && field in requiredFieldLabels,
  );
}

function invalidFieldsFromApi(error: unknown): RequiredNeedField[] {
  if (!(error instanceof ApiError) || error.code !== "REQUEST_VALIDATION_FAILED") return [];
  if (!Array.isArray(error.details)) return [];
  return error.details.flatMap((detail) => {
    if (!detail || typeof detail !== "object" || !Array.isArray((detail as { loc?: unknown }).loc)) return [];
    const field = [...(detail as { loc: unknown[] }).loc].reverse().find(
      (part): part is RequiredNeedField => typeof part === "string" && part in requiredFieldLabels,
    );
    return field ? [field] : [];
  });
}

function getInvalidNumberFields(values: TrainingNeedInput): RequiredNeedField[] {
  const integerFields: RequiredNeedField[] = ["participant_count", "duration_hours", "planned_days_count"];
  return integerFields.filter((field) => {
    const value = values[field];
    return typeof value === "number" && (!Number.isInteger(value) || value < 1);
  });
}

export function calculateDesiredEndDate(
  startDate: string | null | undefined,
  plannedDaysCount: number | null | undefined,
): string | null {
  if (!startDate || !Number.isInteger(plannedDaysCount) || plannedDaysCount! < 1) return null;
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(startDate);
  if (!match) return null;
  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  const date = new Date(Date.UTC(year, month - 1, day));
  if (date.getUTCFullYear() !== year || date.getUTCMonth() !== month - 1 || date.getUTCDate() !== day) return null;
  date.setUTCDate(date.getUTCDate() + plannedDaysCount! - 1);
  return date.toISOString().slice(0, 10);
}

export function TrainingNeedSection({ caseId, onChanged }: { caseId: string; onChanged: () => void | Promise<void> }) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: ["training-need", caseId],
    queryFn: () => getTrainingNeed(caseId),
    retry: false,
  });
  const [values, setValues] = useState<TrainingNeedInput>(emptyNeed);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Partial<Record<RequiredNeedField, string>>>({});
  const notFound = query.error instanceof ApiError && query.error.status === 404;

  /* eslint-disable react-hooks/set-state-in-effect -- server data resets the editable form */
  useEffect(() => {
    // La réponse serveur devient la nouvelle référence après création ou sauvegarde.
    if (query.data) {
      setValues({ ...emptyNeed, ...query.data });
      setFieldErrors({});
    }
  }, [query.data]);
  /* eslint-enable react-hooks/set-state-in-effect */

  const refresh = async () => {
    await queryClient.invalidateQueries({ queryKey: ["training-need", caseId] });
    await onChanged();
  };
  const completeAndGenerate = useMutation({
    mutationFn: async () => {
      if (query.data) {
        await updateTrainingNeed(caseId, values);
      } else {
        await createTrainingNeed(caseId, values);
      }
      await validateTrainingNeed(caseId);
      return generateTrainingProgramDraft(caseId);
    },
    onSuccess: async (program) => {
      queryClient.setQueryData(["training-program", caseId], program);
      await refresh();
      router.push(`/dossiers/${caseId}?step=5&program=generated`);
    },
    onError: (error) => {
      const missingFields = missingFieldsFromApi(error);
      if (missingFields.length) {
        showMissingFields(missingFields);
        return;
      }
      const invalidFields = invalidFieldsFromApi(error);
      if (invalidFields.length) showInvalidNumberFields(invalidFields);
    },
  });

  const update = (field: keyof TrainingNeedInput, value: string) => {
    setValidationError(null);
    setFieldErrors((current) => ({ ...current, [field]: undefined }));
    if (field === "participant_count" || field === "duration_hours" || field === "planned_days_count") {
      const numericValue = value === "" ? null : Number(value);
      setValues((current) => ({
        ...current,
        [field]: numericValue,
        ...(field === "planned_days_count" ? {
          desired_end_date: calculateDesiredEndDate(current.desired_start_date, numericValue),
        } : {}),
      }));
      return;
    }
    setValues((current) => ({
      ...current,
      [field]: value || null,
      ...(field === "desired_start_date" ? {
        desired_end_date: calculateDesiredEndDate(value, current.planned_days_count),
      } : {}),
    }));
  };

  function showMissingFields(missingFields: RequiredNeedField[]) {
    setFieldErrors(Object.fromEntries(
      missingFields.map((field) => [field, "Ce champ obligatoire doit être renseigné."]),
    ));
    setValidationError(
      `Champs obligatoires manquants : ${missingFields.map((field) => requiredFieldLabels[field]).join(", ")}.`,
    );
    queueMicrotask(() => document.getElementById(`training-need-${missingFields[0]}`)?.focus());
  }

  function showInvalidNumberFields(invalidFields: RequiredNeedField[]) {
    setFieldErrors(Object.fromEntries(
      invalidFields.map((field) => [field, "Saisissez un nombre entier supérieur ou égal à 1."]),
    ));
    setValidationError(
      `Valeur invalide : ${invalidFields.map((field) => requiredFieldLabels[field]).join(", ")}.`,
    );
    queueMicrotask(() => document.getElementById(`training-need-${invalidFields[0]}`)?.focus());
  }

  const requestValidation = () => {
    const missingFields = getMissingRequiredFields(values);
    if (missingFields.length) {
      showMissingFields(missingFields);
      return;
    }
    const invalidNumberFields = getInvalidNumberFields(values);
    if (invalidNumberFields.length) {
      showInvalidNumberFields(invalidNumberFields);
      return;
    }
    if (values.desired_end_date! < values.desired_start_date!) {
      setValidationError("La date de fin doit suivre la date de début.");
      return;
    }
    setValidationError(null);
    completeAndGenerate.mutate();
  };

  if (query.isPending) return <p role="status">Chargement du besoin client…</p>;
  if (query.isError && !notFound) {
    return <p role="alert" className="text-sm text-red-700">{query.error instanceof ApiError ? query.error.message : "Impossible de charger le besoin client."}</p>;
  }

  const readOnly = query.data?.is_validated === true;
  const actionError = completeAndGenerate.error;

  return (
    <section className="mt-6 rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="font-bold text-blue-800">Besoin du client</h2>
          <p className="mt-1 text-xs text-slate-500">
            {readOnly ? `Validé le ${new Date(query.data!.validated_at!).toLocaleString("fr-FR")}` : "Renseignez le besoin, puis enregistrez-le pour générer directement le programme."}
          </p>
        </div>
        <span className={`rounded px-2 py-1 text-xs font-semibold ${readOnly ? "bg-green-50 text-green-700" : "bg-amber-50 text-amber-700"}`}>{readOnly ? "Validé" : "À compléter"}</span>
      </div>

      <fieldset disabled={readOnly || completeAndGenerate.isPending} className="mt-5 grid gap-5">
        <NeedGroup title="Participants" description="Définissez le public et le niveau de la formation.">
        <TextField field="target_audience" label="Public cible *" value={values.target_audience} error={fieldErrors.target_audience} onChange={(value) => update("target_audience", value)} />
        <label className="grid gap-1.5 text-xs font-semibold">Niveau *
          <select id="training-need-level" aria-label="Niveau" aria-invalid={Boolean(fieldErrors.level)} aria-describedby={fieldErrors.level ? "training-need-level-error" : undefined} value={values.level ?? ""} onChange={(event) => update("level", event.target.value)} className={`rounded-md border px-3 py-2.5 font-normal ${fieldErrors.level ? "border-red-600 bg-red-50 ring-1 ring-red-600" : "border-slate-300"}`}>
            <option value="">Sélectionner</option>
            {trainingNeedLevels.map((level) => <option key={level} value={level}>{levelLabels[level]}</option>)}
          </select>
          {fieldErrors.level && <span id="training-need-level-error" className="text-xs font-normal text-red-700">{fieldErrors.level}</span>}
        </label>
        <TextField field="location" label="Lieu *" value={values.location} error={fieldErrors.location} onChange={(value) => update("location", value)} />
        <NumberField field="participant_count" label="Nombre de participants *" value={values.participant_count} error={fieldErrors.participant_count} onChange={(value) => update("participant_count", value)} />
        </NeedGroup>
        <NeedGroup title="Organisation" description="Planifiez le déroulement et le format de la session.">
        <label className="grid gap-1.5 text-xs font-semibold">Modalité *
          <select id="training-need-delivery_mode" aria-label="Modalité" aria-invalid={Boolean(fieldErrors.delivery_mode)} aria-describedby={fieldErrors.delivery_mode ? "training-need-delivery_mode-error" : undefined} value={values.delivery_mode ?? ""} onChange={(event) => update("delivery_mode", event.target.value)} className={`rounded-md border px-3 py-2.5 font-normal ${fieldErrors.delivery_mode ? "border-red-600 bg-red-50 ring-1 ring-red-600" : "border-slate-300"}`}>
            <option value="">Sélectionner</option>
            {deliveryModes.map((mode) => <option key={mode} value={mode}>{modeLabels[mode]}</option>)}
          </select>
          {fieldErrors.delivery_mode && <span id="training-need-delivery_mode-error" className="text-xs font-normal text-red-700">{fieldErrors.delivery_mode}</span>}
        </label>
        <NumberField field="duration_hours" label="Durée de la formation en heures *" value={values.duration_hours} error={fieldErrors.duration_hours} onChange={(value) => update("duration_hours", value)} min="1" step="1" />
        <NumberField field="planned_days_count" label="Nombre de jours planifiés *" value={values.planned_days_count} error={fieldErrors.planned_days_count} onChange={(value) => update("planned_days_count", value)} min="1" step="1" />
        <TextField field="desired_start_date" label="Début souhaité *" type="date" value={values.desired_start_date} error={fieldErrors.desired_start_date} onChange={(value) => update("desired_start_date", value)} />
        <TextField field="desired_end_date" label="Fin souhaitée *" type="date" value={values.desired_end_date} error={fieldErrors.desired_end_date} readOnly onChange={() => undefined} />
        </NeedGroup>
        <NeedGroup title="Objectifs pédagogiques" description="Indiquez les compétences à développer pendant la formation." single>
        <TextArea field="objectives" label="Objectifs pédagogiques *" value={values.objectives} error={fieldErrors.objectives} onChange={(value) => update("objectives", value)} />
        </NeedGroup>
        <NeedGroup title="Contraintes particulières" description="Ajoutez les éléments logistiques ou pédagogiques à prendre en compte." single>
        <TextArea field="constraints" label="Contraintes particulières" value={values.constraints} onChange={(value) => update("constraints", value)} />
        </NeedGroup>
      </fieldset>

      {!readOnly && <div className="mt-5 flex flex-wrap justify-end gap-3">
        <button type="button" onClick={() => router.push(`/formateurs?case_id=${caseId}`)} disabled={completeAndGenerate.isPending} className="btn btn-secondary">← Retour</button>
        <button type="button" aria-label="Enregistrer et générer le programme" onClick={requestValidation} disabled={completeAndGenerate.isPending} className="rounded-md bg-green-600 px-4 py-2 text-sm font-semibold text-white">{completeAndGenerate.isPending ? "Génération du programme en cours…" : "Enregistrer et générer le programme"}</button>
      </div>}
      {validationError && <p role="alert" className="mt-4 text-sm text-red-700">{validationError}</p>}
      {actionError && !validationError && <p role="alert" className="mt-4 text-sm text-red-700">{actionError instanceof ApiError ? actionError.message : "L’action a échoué."}</p>}
    </section>
  );
}

function NeedGroup({ title, description, children, single = false }: { title: string; description: string; children: ReactNode; single?: boolean }) {
  return <section className="rounded-xl border border-slate-200 bg-slate-50/60 p-4"><div className="mb-4"><h3 className="font-semibold text-slate-900">{title}</h3><p className="mt-1 text-xs text-slate-500">{description}</p></div><div className={single ? "grid gap-4" : "grid gap-4 md:grid-cols-2"}>{children}</div></section>;
}

function TextField({ field, label, value, onChange, type = "text", readOnly = false, error }: { field: keyof TrainingNeedInput; label: string; value: string | null | undefined; onChange: (value: string) => void; type?: "text" | "date"; readOnly?: boolean; error?: string }) {
  const id = `training-need-${field}`;
  return <label className="grid gap-1.5 text-xs font-semibold">{label}<input id={id} aria-label={label.replace(" *", "")} aria-invalid={Boolean(error)} aria-describedby={error ? `${id}-error` : undefined} type={type} value={value ?? ""} readOnly={readOnly} onChange={(event) => onChange(event.target.value)} className={`rounded-md border px-3 py-2.5 font-normal read-only:bg-slate-100 read-only:text-slate-600 ${error ? "border-red-600 bg-red-50 ring-1 ring-red-600" : "border-slate-300"}`} />{error && <span id={`${id}-error`} className="text-xs font-normal text-red-700">{error}</span>}</label>;
}

function NumberField({ field, label, value, onChange, min = "1", step = "1", error }: { field: keyof TrainingNeedInput; label: string; value: number | null | undefined; onChange: (value: string) => void; min?: string; step?: string; error?: string }) {
  const id = `training-need-${field}`;
  return <label className="grid gap-1.5 text-xs font-semibold">{label}<input id={id} aria-label={label.replace(" *", "")} aria-invalid={Boolean(error)} aria-describedby={error ? `${id}-error` : undefined} type="number" min={min} step={step} value={value ?? ""} onChange={(event) => onChange(event.target.value)} className={`rounded-md border px-3 py-2.5 font-normal ${error ? "border-red-600 bg-red-50 ring-1 ring-red-600" : "border-slate-300"}`} />{error && <span id={`${id}-error`} className="text-xs font-normal text-red-700">{error}</span>}</label>;
}

function TextArea({ field, label, value, onChange, error }: { field: keyof TrainingNeedInput; label: string; value: string | null | undefined; onChange: (value: string) => void; error?: string }) {
  const id = `training-need-${field}`;
  return <label className="grid gap-1.5 text-xs font-semibold">{label}<textarea id={id} aria-label={label.replace(" *", "")} aria-invalid={Boolean(error)} aria-describedby={error ? `${id}-error` : undefined} rows={4} value={value ?? ""} onChange={(event) => onChange(event.target.value)} className={`rounded-md border px-3 py-2.5 font-normal ${error ? "border-red-600 bg-red-50 ring-1 ring-red-600" : "border-slate-300"}`} />{error && <span id={`${id}-error`} className="text-xs font-normal text-red-700">{error}</span>}</label>;
}
