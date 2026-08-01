"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";

import {
  createTrainingPricing,
  getTrainingPricing,
  returnTrainingPricing,
  submitTrainingPricing,
  updateTrainingPricing,
  validateTrainingPricing,
} from "@/features/training-pricings/api";
import { ApiError } from "@/lib/api";
import {
  allowedVatRates,
  type TrainingPricing,
  type TrainingPricingInput,
  type VatRate,
} from "@/types/training-pricing";

const initializationLabels = {
  DAILY_RATE: "Tarif journalier × nombre de journées",
  HOURLY_RATE: "Tarif horaire × durée du programme",
  NONE: "Aucun tarif formateur disponible",
};

export function TrainingPricingSection({
  caseId,
  onChanged,
}: {
  caseId: string;
  onChanged: () => void;
}) {
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: ["training-pricing", caseId],
    queryFn: () => getTrainingPricing(caseId),
    retry: false,
  });
  const notFound = query.error instanceof ApiError && query.error.status === 404;
  const [values, setValues] = useState<TrainingPricingInput | null>(null);
  const [returnReason, setReturnReason] = useState("");

  useEffect(() => {
    if (!query.data) return;
    // La réponse serveur remplace les calculs prévisionnels après chaque sauvegarde.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setValues(toInput(query.data));
  }, [query.data]);

  const apply = (pricing: TrainingPricing) => {
    queryClient.setQueryData(["training-pricing", caseId], pricing);
    setValues(toInput(pricing));
    onChanged();
  };
  const create = useMutation({
    mutationFn: () => createTrainingPricing(caseId),
    onSuccess: apply,
  });
  const action = useMutation({
    mutationFn: (operation: () => Promise<TrainingPricing>) => operation(),
    onSuccess: apply,
  });
  const preview = useMemo(() => calculatePreview(values), [values]);

  if (query.isPending) return <p role="status">Chargement de la tarification…</p>;
  if (notFound) {
    return (
      <section className="mt-6 rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="font-bold text-blue-800">9. Tarification</h2>
        <p className="mt-2 text-sm text-slate-500">
          Le programme est validé. Vous pouvez maintenant préparer la tarification.
        </p>
        <button
          type="button"
          onClick={() => create.mutate()}
          disabled={create.isPending}
          className="mt-4 rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white"
        >
          {create.isPending ? "Création…" : "Créer la tarification"}
        </button>
        {create.error && <ErrorMessage error={create.error} />}
      </section>
    );
  }
  if (!query.data || !values || query.isError) return <ErrorMessage error={query.error} />;

  const pricing = query.data;
  const editable = pricing.editable;
  const totals = editable ? preview : serverTotals(pricing);
  const zeroVatMissing =
    values.vat_rate === "0.000" &&
    !values.vat_exemption_reason?.trim() &&
    !values.vat_legal_reference?.trim();

  return (
    <section className="mt-6 rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="font-bold text-blue-800">9. Tarification</h2>
          <p className="mt-1 text-xs text-slate-500">
            {pricing.is_validated
              ? `Validée le ${new Date(pricing.validated_at!).toLocaleString("fr-FR")}. Lecture seule définitive.`
              : pricing.is_submitted
                ? "En attente de validation. Les montants sont verrouillés."
                : "Les calculs affichés avant enregistrement sont prévisionnels."}
          </p>
        </div>
        <span
          className={`rounded px-2 py-1 text-xs font-semibold ${
            pricing.is_validated
              ? "bg-green-50 text-green-700"
              : pricing.is_submitted
                ? "bg-amber-50 text-amber-700"
                : "bg-blue-50 text-blue-700"
          }`}
        >
          {pricing.is_validated
            ? "Tarification validée"
            : pricing.is_submitted
              ? "En attente de validation"
              : "En préparation"}
        </span>
      </div>

      <div className="mt-5 grid gap-5 lg:grid-cols-2">
        <article className="rounded-lg border border-slate-200 p-5">
          <h3 className="font-bold text-slate-900">Détails des coûts</h3>
          <p className="mt-1 text-xs text-slate-500">
            Origine initiale :{" "}
            {initializationLabels[pricing.trainer_cost_initialization_method]}
          </p>
          {pricing.trainer_cost_initialization_method === "NONE" && (
            <p className="mt-3 rounded bg-amber-50 p-2 text-xs text-amber-800">
              Aucun tarif formateur n’était disponible. Vérifiez le coût saisi.
            </p>
          )}
          <fieldset disabled={!editable || action.isPending} className="mt-4 grid gap-3">
            <MoneyField
              label="Coût formateur"
              value={values.trainer_cost}
              onChange={(value) => updateValue(setValues, "trainer_cost", value)}
            />
            <MoneyField
              label="Transport"
              value={values.transport_cost}
              onChange={(value) => updateValue(setValues, "transport_cost", value)}
            />
            <MoneyField
              label="Salle"
              value={values.room_cost}
              onChange={(value) => updateValue(setValues, "room_cost", value)}
            />
            <MoneyField
              label="Repas"
              value={values.meal_cost}
              onChange={(value) => updateValue(setValues, "meal_cost", value)}
            />
            <MoneyField
              label="Autres frais"
              value={values.other_cost}
              onChange={(value) => updateValue(setValues, "other_cost", value)}
            />
          </fieldset>
          <TotalRow label="Total des coûts" value={totals.totalCosts} strong />
        </article>

        <article className="rounded-lg border border-slate-200 p-5">
          <h3 className="font-bold text-slate-900">Calcul du prix</h3>
          <fieldset disabled={!editable || action.isPending} className="mt-4 grid gap-3">
            <RateField
              label="Marge (%)"
              value={values.margin_rate}
              onChange={(value) => updateValue(setValues, "margin_rate", value)}
            />
            <label className="grid gap-1 text-xs font-semibold">
              Taux de TVA
              <select
                aria-label="Taux de TVA"
                value={values.vat_rate}
                onChange={(event) =>
                  updateValue(setValues, "vat_rate", event.target.value as VatRate)
                }
                className="rounded-md border border-slate-300 px-3 py-2 font-normal"
              >
                {allowedVatRates.map((rate) => (
                  <option key={rate} value={rate}>
                    {rate.replace(".", ",")} %
                  </option>
                ))}
              </select>
            </label>
            {values.vat_rate === "0.000" && (
              <div className="grid gap-3">
                <TextField
                  label="Motif d’exonération"
                  value={values.vat_exemption_reason ?? ""}
                  onChange={(value) =>
                    updateValue(setValues, "vat_exemption_reason", value || null)
                  }
                />
                <TextField
                  label="Référence fiscale"
                  value={values.vat_legal_reference ?? ""}
                  onChange={(value) =>
                    updateValue(setValues, "vat_legal_reference", value || null)
                  }
                />
                {zeroVatMissing && (
                  <p role="alert" className="text-xs text-red-700">
                    Saisissez un motif d’exonération ou une référence fiscale.
                  </p>
                )}
              </div>
            )}
          </fieldset>
          <div className="mt-4 space-y-3">
            <TotalRow label="Montant marge" value={totals.marginAmount} />
            <TotalRow label="Total HT" value={totals.totalExcludingTax} strong />
            <TotalRow
              label={`TVA (${values.vat_rate.replace(".", ",")} %)`}
              value={totals.vatAmount}
            />
            <div className="flex items-center justify-between rounded-md border border-green-200 bg-green-50 p-3 text-green-800">
              <strong>Total TTC</strong>
              <strong className="text-lg">{formatTnd(totals.totalIncludingTax)}</strong>
            </div>
          </div>
        </article>
      </div>

      <p className="mt-4 rounded-md bg-amber-50 p-3 text-xs text-amber-900">
        Vérifiez l’applicabilité fiscale du taux sélectionné. PrestaCode ne fournit
        aucun conseil fiscal et ne détermine pas le régime applicable.
      </p>
      {pricing.return_reason && !pricing.is_submitted && (
        <p className="mt-3 rounded-md bg-amber-50 p-3 text-sm text-amber-800">
          Motif du retour : {pricing.return_reason}
        </p>
      )}

      <div className="mt-5 flex flex-wrap justify-end gap-3">
        {editable && (
          <>
            <button
              type="button"
              disabled={action.isPending || zeroVatMissing}
              onClick={() => action.mutate(() => updateTrainingPricing(caseId, values))}
              className="rounded-md border border-blue-300 px-4 py-2 text-sm font-semibold text-blue-700"
            >
              Enregistrer
            </button>
            <button
              type="button"
              disabled={action.isPending || zeroVatMissing}
              onClick={() => {
                if (window.confirm("Soumettre cette tarification pour validation ?")) {
                  action.mutate(() =>
                    updateTrainingPricing(caseId, values).then(() =>
                      submitTrainingPricing(caseId),
                    ),
                  );
                }
              }}
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white"
            >
              Soumettre pour validation
            </button>
          </>
        )}
        {pricing.is_submitted && !pricing.is_validated && (
          <>
            <input
              aria-label="Motif du retour"
              value={returnReason}
              onChange={(event) => setReturnReason(event.target.value)}
              placeholder="Motif obligatoire"
              className="rounded-md border border-slate-300 px-3 py-2 text-sm"
            />
            <button
              type="button"
              disabled={action.isPending || !returnReason.trim()}
              onClick={() =>
                action.mutate(() => returnTrainingPricing(caseId, returnReason))
              }
              className="rounded-md border border-amber-300 px-4 py-2 text-sm font-semibold text-amber-800"
            >
              Renvoyer en préparation
            </button>
            <button
              type="button"
              disabled={action.isPending}
              onClick={() => {
                if (window.confirm("Valider définitivement cette tarification ?")) {
                  action.mutate(() => validateTrainingPricing(caseId));
                }
              }}
              className="rounded-md bg-green-600 px-4 py-2 text-sm font-semibold text-white"
            >
              Valider la tarification
            </button>
          </>
        )}
      </div>
      {action.error && <ErrorMessage error={action.error} />}
    </section>
  );
}

function toInput(pricing: TrainingPricing): TrainingPricingInput {
  return {
    trainer_cost: pricing.trainer_cost,
    transport_cost: pricing.transport_cost,
    room_cost: pricing.room_cost,
    meal_cost: pricing.meal_cost,
    other_cost: pricing.other_cost,
    margin_rate: pricing.margin_rate,
    vat_rate: pricing.vat_rate,
    vat_exemption_reason: pricing.vat_exemption_reason,
    vat_legal_reference: pricing.vat_legal_reference,
  };
}

function updateValue<K extends keyof TrainingPricingInput>(
  setter: React.Dispatch<React.SetStateAction<TrainingPricingInput | null>>,
  key: K,
  value: TrainingPricingInput[K],
) {
  setter((current) => (current ? { ...current, [key]: value } : current));
}

function calculatePreview(values: TrainingPricingInput | null) {
  if (!values) return emptyTotals();
  const totalCosts = [
    values.trainer_cost,
    values.transport_cost,
    values.room_cost,
    values.meal_cost,
    values.other_cost,
  ].reduce((total, value) => total + toScaled(value), 0);
  const marginAmount = roundDivide(
    totalCosts * toScaled(values.margin_rate),
    100_000,
  );
  const totalExcludingTax = totalCosts + marginAmount;
  const vatAmount = roundDivide(
    totalExcludingTax * toScaled(values.vat_rate),
    100_000,
  );
  return {
    totalCosts,
    marginAmount,
    totalExcludingTax,
    vatAmount,
    totalIncludingTax: totalExcludingTax + vatAmount,
  };
}

function serverTotals(pricing: TrainingPricing) {
  return {
    totalCosts: toScaled(pricing.total_costs),
    marginAmount: toScaled(pricing.margin_amount),
    totalExcludingTax: toScaled(pricing.total_excluding_tax),
    vatAmount: toScaled(pricing.vat_amount),
    totalIncludingTax: toScaled(pricing.total_including_tax),
  };
}

function emptyTotals() {
  return {
    totalCosts: 0,
    marginAmount: 0,
    totalExcludingTax: 0,
    vatAmount: 0,
    totalIncludingTax: 0,
  };
}

function toScaled(value: string): number {
  const normalized = value.replace(",", ".").trim();
  if (!/^\d*(\.\d{0,3})?$/.test(normalized)) return 0;
  const [whole = "0", fraction = ""] = normalized.split(".");
  return Number(whole || "0") * 1000 + Number(fraction.padEnd(3, "0"));
}

function roundDivide(value: number, divisor: number): number {
  return Math.floor((value + divisor / 2) / divisor);
}

function formatTnd(millimes: number): string {
  return `${new Intl.NumberFormat("fr-FR", {
    minimumFractionDigits: 3,
    maximumFractionDigits: 3,
  }).format(millimes / 1000)} TND`;
}

function MoneyField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="grid grid-cols-[1fr_150px] items-center gap-3 text-xs font-semibold">
      {label}
      <span className="relative">
        <input
          aria-label={label}
          inputMode="decimal"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          className="w-full rounded-md border border-slate-300 px-3 py-2 pr-12 text-right font-normal"
        />
        <span className="absolute right-3 top-2 text-slate-400">TND</span>
      </span>
    </label>
  );
}

function RateField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="grid grid-cols-[1fr_150px] items-center gap-3 text-xs font-semibold">
      {label}
      <input
        aria-label={label}
        inputMode="decimal"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="rounded-md border border-slate-300 px-3 py-2 text-right font-normal"
      />
    </label>
  );
}

function TextField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="grid gap-1 text-xs font-semibold">
      {label}
      <input
        aria-label={label}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="rounded-md border border-slate-300 px-3 py-2 font-normal"
      />
    </label>
  );
}

function TotalRow({
  label,
  value,
  strong = false,
}: {
  label: string;
  value: number;
  strong?: boolean;
}) {
  return (
    <div className={`mt-4 flex justify-between border-t pt-3 text-sm ${strong ? "font-bold" : ""}`}>
      <span>{label}</span>
      <span>{formatTnd(value)}</span>
    </div>
  );
}

function ErrorMessage({ error }: { error: unknown }) {
  return (
    <p role="alert" className="mt-4 text-sm text-red-700">
      {error instanceof ApiError ? error.message : "L’action a échoué."}
    </p>
  );
}
