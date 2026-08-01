"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";

import {
  addProgramDay,
  addProgramItem,
  createTrainingProgram,
  deleteProgramDay,
  deleteProgramItem,
  getTrainingProgram,
  generateTrainingProgramDraft,
  moveProgramDay,
  moveProgramItem,
  returnTrainingProgram,
  submitTrainingProgram,
  updateProgramDay,
  updateProgramItem,
  updateTrainingProgram,
  validateTrainingProgram,
} from "@/features/training-programs/api";
import { ApiError } from "@/lib/api";
import {
  pedagogicalMethods,
  type PedagogicalMethod,
  type ProgramItemInput,
  type TrainingProgram,
  type TrainingProgramItem,
} from "@/types/training-program";

const methodLabels: Record<PedagogicalMethod, string> = {
  EXPOSE: "Exposé",
  DEMONSTRATION: "Démonstration",
  EXERCICE_PRATIQUE: "Exercice pratique",
  ETUDE_DE_CAS: "Étude de cas",
  MISE_EN_SITUATION: "Mise en situation",
  ECHANGE_COLLECTIF: "Échange collectif",
  EVALUATION: "Évaluation",
};

const emptyItem: ProgramItemInput = {
  item_type: "MODULE",
  parent_id: null,
  title: "",
  content: "",
  theory_minutes: 0,
  practice_minutes: 0,
  methods: [],
};

export function TrainingProgramSection({
  caseId,
  caseTheme,
  onChanged,
}: {
  caseId: string;
  caseTheme: string;
  onChanged: () => void;
}) {
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: ["training-program", caseId],
    queryFn: () => getTrainingProgram(caseId),
    retry: false,
  });
  const notFound = query.error instanceof ApiError && query.error.status === 404;
  const [metadata, setMetadata] = useState({
    title: caseTheme,
    general_objectives: "",
    prerequisites: "",
    evaluation_method: "",
  });
  const [selectedDayId, setSelectedDayId] = useState<string | null>(null);
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);
  const [itemInput, setItemInput] = useState<ProgramItemInput>(emptyItem);
  const [returnReason, setReturnReason] = useState("");
  const [generatedNotice, setGeneratedNotice] = useState(false);

  useEffect(() => {
    if (!query.data) return;
    // La version renvoyée par l’API reste la référence après chaque action.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setMetadata({
      title: query.data.title,
      general_objectives: query.data.general_objectives ?? "",
      prerequisites: query.data.prerequisites ?? "",
      evaluation_method: query.data.evaluation_method ?? "",
    });
  }, [query.data]);

  const apply = async (program: TrainingProgram) => {
    queryClient.setQueryData(["training-program", caseId], program);
    onChanged();
  };
  const action = useMutation({
    mutationFn: async (operation: () => Promise<TrainingProgram>) => operation(),
    onSuccess: apply,
  });
  const create = useMutation({
    mutationFn: () =>
      createTrainingProgram(caseId, {
        title: caseTheme,
        general_objectives: "",
        prerequisites: "",
        evaluation_method: "",
      }),
    onSuccess: apply,
  });
  const generate = useMutation({
    mutationFn: () => generateTrainingProgramDraft(caseId),
    onSuccess: async (generatedProgram) => {
      await apply(generatedProgram);
      setGeneratedNotice(true);
    },
  });
  const program = query.data;
  const editable = program ? !program.is_submitted && !program.is_validated : false;
  const selectedItem = useMemo(
    () => (program ? findItem(program, selectedItemId) : null),
    [program, selectedItemId],
  );

  useEffect(() => {
    if (!selectedItem) return;
    // La sélection d’un nœud initialise l’éditeur avec sa valeur serveur.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setItemInput({
      item_type: selectedItem.item_type,
      parent_id: selectedItem.parent_id,
      title: selectedItem.title,
      content: selectedItem.content ?? "",
      theory_minutes: selectedItem.theory_minutes,
      practice_minutes: selectedItem.practice_minutes,
      methods: selectedItem.methods,
    });
  }, [selectedItem]);

  if (query.isPending) return <p role="status">Chargement du programme…</p>;
  if (notFound) {
    return (
      <section className="mt-6 rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="font-bold text-blue-800">8. Programme de formation</h2>
        <p className="mt-2 text-sm text-slate-500">
          Créez manuellement le programme ou demandez à Ollama un brouillon modifiable.
        </p>
        <p className="mt-3 rounded-md bg-blue-50 p-3 text-sm text-blue-800">
          Ollama va proposer un programme modifiable à partir du besoin validé. Le programme ne
          sera ni soumis ni validé automatiquement.
        </p>
        <div className="mt-4 flex flex-wrap gap-3">
          <button type="button" onClick={() => {
            if (window.confirm("Générer un brouillon de programme avec Ollama ? Vous pourrez modifier librement le résultat avant de le soumettre.")) generate.mutate();
          }} disabled={create.isPending || generate.isPending} className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">
            {generate.isPending ? "Génération du programme en cours…" : "Générer un brouillon avec Ollama"}
          </button>
          <button type="button" onClick={() => create.mutate()} disabled={create.isPending || generate.isPending} className="rounded-md border border-blue-300 px-4 py-2 text-sm font-semibold text-blue-700 disabled:opacity-50">
            {create.isPending ? "Création…" : "Créer manuellement"}
          </button>
        </div>
        {generate.isPending && <p role="status" className="mt-3 text-sm text-blue-700">Génération du programme en cours…</p>}
        {(create.error || generate.error) && <ErrorMessage error={create.error ?? generate.error} />}
        {generate.error && <button type="button" onClick={() => generate.mutate()} className="mt-2 text-sm font-semibold text-blue-700 underline">Réessayer</button>}
      </section>
    );
  }
  if (!program || query.isError) {
    return <ErrorMessage error={query.error} />;
  }

  const difference = program.total_minutes - program.expected_total_minutes;
  return (
    <section className="mt-6 rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      {generatedNotice && (
        <p role="status" className="mb-4 rounded-md border border-green-200 bg-green-50 p-3 text-sm text-green-800">
          Brouillon généré par Ollama. Vérifiez et modifiez le contenu avant de le soumettre.
        </p>
      )}
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="font-bold text-blue-800">8. Programme de formation</h2>
          <p className="mt-1 text-xs text-slate-500">
            {program.is_validated
              ? "Programme validé et verrouillé."
              : program.is_submitted
                ? "Programme soumis pour validation."
                : "Construisez les journées, modules et sous-modules."}
          </p>
        </div>
        <span className="rounded bg-blue-50 px-2 py-1 text-xs font-semibold text-blue-700">
          {program.is_validated ? "Validé" : program.is_submitted ? "À valider" : "En préparation"}
        </span>
      </div>

      <div className="mt-5 grid gap-3 rounded-md bg-slate-50 p-4 text-center sm:grid-cols-4">
        <Total label="Durée attendue" value={program.expected_total_minutes} />
        <Total label="Théorie" value={program.theory_total_minutes} />
        <Total label="Pratique" value={program.practice_total_minutes} />
        <Total
          label="Écart"
          value={difference}
          className={difference === 0 ? "text-green-700" : "text-red-700"}
        />
      </div>

      <fieldset disabled={!editable || action.isPending} className="mt-5 grid gap-4 md:grid-cols-2">
        <TextField
          label="Titre du programme"
          value={metadata.title}
          onChange={(value) => setMetadata((current) => ({ ...current, title: value }))}
        />
        <TextArea
          label="Objectifs généraux"
          value={metadata.general_objectives}
          onChange={(value) =>
            setMetadata((current) => ({ ...current, general_objectives: value }))
          }
        />
        <TextArea
          label="Prérequis"
          value={metadata.prerequisites}
          onChange={(value) =>
            setMetadata((current) => ({ ...current, prerequisites: value }))
          }
        />
        <TextArea
          label="Méthode d’évaluation"
          value={metadata.evaluation_method}
          onChange={(value) =>
            setMetadata((current) => ({ ...current, evaluation_method: value }))
          }
        />
      </fieldset>
      {editable && (
        <div className="mt-3 flex justify-end">
          <button
            type="button"
            onClick={() => action.mutate(() => updateTrainingProgram(caseId, metadata))}
            className="rounded-md border border-blue-300 px-4 py-2 text-sm font-semibold text-blue-700"
          >
            Enregistrer les informations
          </button>
        </div>
      )}

      <div className="mt-6 grid gap-5 lg:grid-cols-[0.9fr_1.4fr]">
        <div className="rounded-md border border-slate-200">
          <div className="flex items-center justify-between border-b p-3">
            <h3 className="font-semibold">Structure du programme</h3>
            {editable && (
              <button
                type="button"
                onClick={() => action.mutate(() => addProgramDay(caseId))}
                className="rounded bg-blue-600 px-3 py-1.5 text-xs font-semibold text-white"
              >
                Ajouter une journée
              </button>
            )}
          </div>
          {program.days.length === 0 && (
            <p className="p-4 text-sm text-slate-500">Aucune journée.</p>
          )}
          <div className="divide-y">
            {program.days.map((day, dayIndex) => (
              <div key={day.id} className="p-3">
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setSelectedDayId(day.id)}
                    className="min-w-0 flex-1 text-left text-sm font-semibold"
                  >
                    Jour {day.position} · {day.title}
                    <span className="ml-2 text-xs font-normal text-slate-500">
                      {formatMinutes(day.total_minutes)}
                    </span>
                  </button>
                  {editable && (
                    <OrderButtons
                      first={dayIndex === 0}
                      last={dayIndex === program.days.length - 1}
                      onUp={() => action.mutate(() => moveProgramDay(caseId, day.id, "up"))}
                      onDown={() => action.mutate(() => moveProgramDay(caseId, day.id, "down"))}
                    />
                  )}
                </div>
                <div className="mt-2 space-y-1 pl-3">
                  {day.items.map((item, itemIndex) => (
                    <ProgramTreeItem
                      key={item.id}
                      item={item}
                      editable={editable}
                      first={itemIndex === 0}
                      last={itemIndex === day.items.length - 1}
                      onSelect={(selected) => {
                        setSelectedDayId(day.id);
                        setSelectedItemId(selected.id);
                      }}
                      onMove={(selected, direction) =>
                        action.mutate(() => moveProgramItem(caseId, selected.id, direction))
                      }
                    />
                  ))}
                </div>
                {editable && selectedDayId === day.id && (
                  <div className="mt-3 flex flex-wrap gap-2">
                    <button
                      type="button"
                      onClick={() => {
                        const title = window.prompt("Titre de la journée", day.title);
                        if (title?.trim()) {
                          action.mutate(() => updateProgramDay(caseId, day.id, title));
                        }
                      }}
                      className="text-xs font-semibold text-blue-700"
                    >
                      Renommer
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setSelectedItemId(null);
                        setItemInput({ ...emptyItem });
                      }}
                      className="text-xs font-semibold text-blue-700"
                    >
                      + Module
                    </button>
                    <button
                      type="button"
                      onClick={() => action.mutate(() => deleteProgramDay(caseId, day.id))}
                      className="text-xs font-semibold text-red-700"
                    >
                      Supprimer
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-md border border-slate-200 p-4">
          {!selectedDayId && (
            <p className="text-sm text-slate-500">
              Sélectionnez une journée ou un module pour afficher l’éditeur.
            </p>
          )}
          {selectedDayId && editable && (
            <ItemEditor
              value={itemInput}
              selected={selectedItem}
              onChange={setItemInput}
              onSave={() => {
                if (!itemInput.title.trim()) return;
                action.mutate(() =>
                  selectedItem
                    ? updateProgramItem(caseId, selectedItem.id, itemInput)
                    : addProgramItem(caseId, selectedDayId, itemInput),
                );
              }}
              onAddChild={
                selectedItem?.item_type === "MODULE"
                  ? () => {
                      setSelectedItemId(null);
                      setItemInput({
                        ...emptyItem,
                        item_type: "SUBMODULE",
                        parent_id: selectedItem.id,
                      });
                    }
                  : undefined
              }
              onDelete={
                selectedItem
                  ? () => {
                      action.mutate(() => deleteProgramItem(caseId, selectedItem.id));
                      setSelectedItemId(null);
                      setItemInput({ ...emptyItem });
                    }
                  : undefined
              }
            />
          )}
          {selectedDayId && !editable && selectedItem && <ReadOnlyItem item={selectedItem} />}
        </div>
      </div>

      {program.return_reason && !program.is_submitted && (
        <p className="mt-4 rounded-md bg-amber-50 p-3 text-sm text-amber-800">
          Motif du retour : {program.return_reason}
        </p>
      )}
      <div className="mt-5 flex flex-wrap justify-end gap-3">
        {editable && (
          <button
            type="button"
            onClick={() => {
              if (window.confirm("Soumettre ce programme pour validation ?")) {
                action.mutate(() => submitTrainingProgram(caseId));
              }
            }}
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white"
          >
            Soumettre pour validation
          </button>
        )}
        {program.is_submitted && !program.is_validated && (
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
              disabled={!returnReason.trim()}
              onClick={() => action.mutate(() => returnTrainingProgram(caseId, returnReason))}
              className="rounded-md border border-amber-300 px-4 py-2 text-sm font-semibold text-amber-800"
            >
              Retourner en préparation
            </button>
            <button
              type="button"
              onClick={() => action.mutate(() => validateTrainingProgram(caseId))}
              className="rounded-md bg-green-600 px-4 py-2 text-sm font-semibold text-white"
            >
              Valider le programme
            </button>
          </>
        )}
      </div>
      {action.error && <ErrorMessage error={action.error} />}
    </section>
  );
}

function ProgramTreeItem({
  item,
  editable,
  first,
  last,
  onSelect,
  onMove,
}: {
  item: TrainingProgramItem;
  editable: boolean;
  first: boolean;
  last: boolean;
  onSelect: (item: TrainingProgramItem) => void;
  onMove: (item: TrainingProgramItem, direction: "up" | "down") => void;
}) {
  return (
    <div>
      <div className="flex items-center gap-2 rounded px-2 py-1 hover:bg-slate-50">
        <button type="button" onClick={() => onSelect(item)} className="min-w-0 flex-1 text-left text-xs">
          {item.position}. {item.title} · {formatMinutes(item.total_minutes)}
        </button>
        {editable && (
          <OrderButtons
            first={first}
            last={last}
            onUp={() => onMove(item, "up")}
            onDown={() => onMove(item, "down")}
          />
        )}
      </div>
      <div className="ml-5">
        {item.children.map((child, index) => (
          <ProgramTreeItem
            key={child.id}
            item={child}
            editable={editable}
            first={index === 0}
            last={index === item.children.length - 1}
            onSelect={onSelect}
            onMove={onMove}
          />
        ))}
      </div>
    </div>
  );
}

function ItemEditor({
  value,
  selected,
  onChange,
  onSave,
  onAddChild,
  onDelete,
}: {
  value: ProgramItemInput;
  selected: TrainingProgramItem | null;
  onChange: (value: ProgramItemInput) => void;
  onSave: () => void;
  onAddChild?: () => void;
  onDelete?: () => void;
}) {
  const hasChildren = Boolean(selected?.children.length);
  return (
    <>
      <h3 className="font-semibold">{selected ? "Modifier l’élément" : "Ajouter un élément"}</h3>
      <div className="mt-4 grid gap-4">
        <TextField
          label="Titre"
          value={value.title}
          onChange={(title) => onChange({ ...value, title })}
        />
        <TextArea
          label="Contenu"
          value={value.content ?? ""}
          onChange={(content) => onChange({ ...value, content })}
        />
        <div className="grid grid-cols-2 gap-3">
          <NumberField
            label="Théorie (minutes)"
            value={value.theory_minutes}
            disabled={hasChildren}
            onChange={(theory_minutes) => onChange({ ...value, theory_minutes })}
          />
          <NumberField
            label="Pratique (minutes)"
            value={value.practice_minutes}
            disabled={hasChildren}
            onChange={(practice_minutes) => onChange({ ...value, practice_minutes })}
          />
        </div>
        <fieldset>
          <legend className="text-xs font-semibold">Méthodes pédagogiques</legend>
          <div className="mt-2 flex flex-wrap gap-2">
            {pedagogicalMethods.map((method) => (
              <label key={method} className="rounded bg-slate-100 px-2 py-1 text-xs">
                <input
                  type="checkbox"
                  checked={value.methods.includes(method)}
                  onChange={(event) =>
                    onChange({
                      ...value,
                      methods: event.target.checked
                        ? [...value.methods, method]
                        : value.methods.filter((value) => value !== method),
                    })
                  }
                  className="mr-1"
                />
                {methodLabels[method]}
              </label>
            ))}
          </div>
        </fieldset>
      </div>
      <div className="mt-4 flex flex-wrap justify-end gap-2">
        {onDelete && (
          <button type="button" onClick={onDelete} className="text-sm font-semibold text-red-700">
            Supprimer
          </button>
        )}
        {onAddChild && (
          <button
            type="button"
            onClick={onAddChild}
            className="rounded-md border border-blue-300 px-3 py-2 text-sm font-semibold text-blue-700"
          >
            Ajouter un sous-module
          </button>
        )}
        <button
          type="button"
          onClick={onSave}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white"
        >
          Enregistrer
        </button>
      </div>
    </>
  );
}

function ReadOnlyItem({ item }: { item: TrainingProgramItem }) {
  return (
    <div>
      <h3 className="font-semibold">{item.title}</h3>
      <p className="mt-3 whitespace-pre-wrap text-sm text-slate-700">{item.content}</p>
      <p className="mt-3 text-xs text-slate-500">
        Théorie {formatMinutes(item.theory_total_minutes)} · Pratique{" "}
        {formatMinutes(item.practice_total_minutes)}
      </p>
    </div>
  );
}

function findItem(program: TrainingProgram, id: string | null): TrainingProgramItem | null {
  if (!id) return null;
  for (const day of program.days) {
    for (const item of day.items) {
      if (item.id === id) return item;
      const child = item.children.find((value) => value.id === id);
      if (child) return child;
    }
  }
  return null;
}

function Total({
  label,
  value,
  className = "",
}: {
  label: string;
  value: number;
  className?: string;
}) {
  return (
    <div>
      <p className="text-xs text-slate-500">{label}</p>
      <strong className={className}>{formatMinutes(value)}</strong>
    </div>
  );
}

function OrderButtons({
  first,
  last,
  onUp,
  onDown,
}: {
  first: boolean;
  last: boolean;
  onUp: () => void;
  onDown: () => void;
}) {
  return (
    <span className="flex gap-1">
      <button type="button" aria-label="Monter" disabled={first} onClick={onUp}>
        ↑
      </button>
      <button type="button" aria-label="Descendre" disabled={last} onClick={onDown}>
        ↓
      </button>
    </span>
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
    <label className="grid gap-1.5 text-xs font-semibold">
      {label}
      <input
        aria-label={label}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="rounded-md border border-slate-300 px-3 py-2.5 font-normal"
      />
    </label>
  );
}

function TextArea({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="grid gap-1.5 text-xs font-semibold">
      {label}
      <textarea
        aria-label={label}
        rows={4}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="rounded-md border border-slate-300 px-3 py-2.5 font-normal"
      />
    </label>
  );
}

function NumberField({
  label,
  value,
  disabled,
  onChange,
}: {
  label: string;
  value: number;
  disabled: boolean;
  onChange: (value: number) => void;
}) {
  return (
    <label className="grid gap-1.5 text-xs font-semibold">
      {label}
      <input
        aria-label={label}
        type="number"
        min="0"
        step="1"
        disabled={disabled}
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
        className="rounded-md border border-slate-300 px-3 py-2.5 font-normal"
      />
    </label>
  );
}

function ErrorMessage({ error }: { error: unknown }) {
  return (
    <p role="alert" className="mt-4 text-sm text-red-700">
      {error instanceof ApiError ? error.message : "L’action a échoué."}
    </p>
  );
}

function formatMinutes(minutes: number): string {
  const sign = minutes < 0 ? "−" : "";
  const absolute = Math.abs(minutes);
  const hours = Math.floor(absolute / 60);
  const remainder = absolute % 60;
  return remainder ? `${sign}${hours} h ${remainder} min` : `${sign}${hours} h`;
}
