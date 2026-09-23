"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import {
  addProgramDay,
  addProgramItem,
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
import { getTrainingNeed } from "@/features/training-needs/api";
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
  const needQuery = useQuery({
    queryKey: ["training-need", caseId],
    queryFn: () => getTrainingNeed(caseId),
    retry: false,
  });
  const notFound = query.error instanceof ApiError && query.error.status === 404;
  const needNotFound = needQuery.error instanceof ApiError && needQuery.error.status === 404;
  const [metadata, setMetadata] = useState({
    title: caseTheme,
    general_objectives: "",
    prerequisites: "",
    evaluation_method: "",
  });
  const [selectedDayId, setSelectedDayId] = useState<string | null>(null);
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);
  const [isCreatingItem, setIsCreatingItem] = useState(false);
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

  if (query.isPending || needQuery.isPending) return <p role="status">Chargement du programme…</p>;
  if (notFound) {
    const needIsValid = Boolean(needQuery.data?.is_validated);
    return (
      <section className="mt-6 rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="font-bold text-blue-800">Programme de formation</h2>
        {!needIsValid && <p role="alert" className="mt-3 rounded-md bg-amber-50 p-3 text-sm text-amber-800">
          {needNotFound
            ? "Incohérence du dossier : aucun besoin client n’est associé. Revenez à l’étape Besoin pour le compléter et le valider."
            : "Le besoin client doit être complètement renseigné et validé avant de préparer le programme."}
        </p>}
        {needIsValid && <><p className="mt-2 text-sm text-slate-500">
          Générez le programme avec Ollama à partir du besoin validé.
        </p>
        <p className="mt-3 rounded-md bg-blue-50 p-3 text-sm text-blue-800">
          Ollama va proposer un programme modifiable à partir du besoin validé.
        </p>
        <div className="mt-4 flex flex-wrap gap-3">
          <Link href={`/dossiers/${caseId}?step=3`} className="rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700">
            Retour au besoin
          </Link>
          <button type="button" onClick={() => generate.mutate()} disabled={generate.isPending} className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">
            {generate.isPending ? "Génération du programme en cours…" : "Générer le programme"}
          </button>
        </div>
        {generate.isPending && <p role="status" className="mt-3 text-sm text-blue-700">Génération du programme en cours…</p>}
        {generate.error && <ErrorMessage error={generate.error} />}
        {generate.error && <button type="button" onClick={() => generate.mutate()} className="mt-2 text-sm font-semibold text-blue-700 underline">Réessayer</button>}
        </>}
      </section>
    );
  }
  if (!program || query.isError) {
    return <ErrorMessage error={query.error} />;
  }

  const difference = program.total_minutes - program.expected_total_minutes;
  const titleWarning = titlesSeemDifferent(caseTheme, metadata.title);
  return (
    <section className="mx-auto mt-6 max-w-[1480px] rounded-2xl border border-slate-200 bg-white p-5 shadow-sm lg:p-7">
      {generatedNotice && (
        <p role="status" className={`mb-4 rounded-md border p-3 text-sm ${program.pedagogical_warning ? "border-amber-200 bg-amber-50 text-amber-800" : "border-green-200 bg-green-50 text-green-800"}`}>
          {program.pedagogical_warning ??
            "Brouillon généré par Ollama. Vérifiez et modifiez le contenu avant de le soumettre."}
        </p>
      )}
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="font-bold text-blue-800">Programme de formation</h2>
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

      <div className="mt-5 grid overflow-hidden rounded-xl border border-slate-200 bg-slate-50 sm:grid-cols-4 sm:divide-x sm:divide-slate-200">
        <Total label="Durée attendue" value={program.expected_total_minutes} />
        <Total label="Théorie" value={program.theory_total_minutes} />
        <Total label="Pratique" value={program.practice_total_minutes} />
        <Total
          label="Écart"
          value={difference}
          className={difference === 0 ? "text-green-700" : "text-red-700"}
        />
      </div>

      <section className="mt-6 rounded-xl border border-slate-200 bg-slate-50/50 p-4 lg:p-5" aria-labelledby="program-general-heading">
      <h3 id="program-general-heading" className="text-base font-bold text-slate-900">Informations générales du programme</h3>
      <fieldset disabled={!editable || action.isPending} className="mt-4 grid gap-4 md:grid-cols-2">
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
      {titleWarning && <p role="status" className="mt-3 flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800"><span aria-hidden="true">⚠</span>Le titre du programme semble différent du thème de la formation.</p>}
      <ObjectivePreview value={metadata.general_objectives} />
      </section>

      <div className="mt-6 grid gap-5 lg:grid-cols-[minmax(330px,0.9fr)_minmax(460px,1.35fr)]">
        <section className="overflow-hidden rounded-xl border border-slate-200 bg-slate-50/40" aria-labelledby="program-structure-heading">
          <div className="flex items-center justify-between gap-3 border-b border-slate-200 bg-white p-4">
            <div><h3 id="program-structure-heading" className="font-bold text-slate-900">Structure du programme</h3><p className="mt-1 text-xs text-slate-500">{program.days.length} journée{program.days.length > 1 ? "s" : ""}</p></div>
            {editable && (
              <button
                type="button"
                onClick={() => action.mutate(() => addProgramDay(caseId))}
                className="btn btn-primary px-3 py-2 text-xs"
              >
                Ajouter une journée
              </button>
            )}
          </div>
          {program.days.length === 0 && (
            <p className="p-4 text-sm text-slate-500">Aucune journée.</p>
          )}
          <div className="divide-y divide-slate-200">
            {program.days.map((day, dayIndex) => (
              <div key={day.id} className="p-4">
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setSelectedDayId(day.id)}
                    className="min-w-0 flex-1 rounded-md text-left text-sm font-bold text-slate-800 focus:outline-none focus:ring-2 focus:ring-violet-500"
                  >
                    Jour {day.position} — {day.title}
                    <span className="ml-2 whitespace-nowrap text-xs font-semibold text-violet-700">
                      {formatMinutes(day.total_minutes)}
                    </span>
                  </button>
                  {editable && (
                    <ActionMenu
                      first={dayIndex === 0}
                      last={dayIndex === program.days.length - 1}
                      onUp={() => action.mutate(() => moveProgramDay(caseId, day.id, "up"))}
                      onDown={() => action.mutate(() => moveProgramDay(caseId, day.id, "down"))}
                      onDelete={() => action.mutate(() => deleteProgramDay(caseId, day.id))}
                    />
                  )}
                </div>
                <div className="mt-2 space-y-1 pl-3">
                  {day.items.map((item, itemIndex) => (
                    <ProgramTreeItem
                      key={item.id}
                      item={item}
                      editable={editable}
                      selectedId={selectedItemId}
                      first={itemIndex === 0}
                      last={itemIndex === day.items.length - 1}
                      onSelect={(selected) => {
                        setSelectedDayId(day.id);
                        setSelectedItemId(selected.id);
                        setIsCreatingItem(false);
                      }}
                      onMove={(selected, direction) =>
                        action.mutate(() => moveProgramItem(caseId, selected.id, direction))
                      }
                      onDelete={(selected) => {
                        action.mutate(() => deleteProgramItem(caseId, selected.id));
                        if (selectedItemId === selected.id) setSelectedItemId(null);
                      }}
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
                        setIsCreatingItem(true);
                      }}
                      className="text-xs font-semibold text-blue-700"
                    >
                      + Module
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>

        <section className="min-h-[360px] rounded-xl border border-slate-200 bg-white p-5 shadow-sm" aria-label="Éditeur du module">
          {(!selectedDayId || (!selectedItem && !isCreatingItem)) && (
            <EmptyEditor />
          )}
          {selectedDayId && editable && (selectedItem || isCreatingItem) && (
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
                      setIsCreatingItem(true);
                    }
                  : undefined
              }
              onDelete={
                selectedItem
                  ? () => {
                      action.mutate(() => deleteProgramItem(caseId, selectedItem.id));
                      setSelectedItemId(null);
                      setItemInput({ ...emptyItem });
                      setIsCreatingItem(false);
                    }
                  : undefined
              }
            />
          )}
          {selectedDayId && !editable && selectedItem && <ReadOnlyItem item={selectedItem} />}
        </section>
      </div>

      {program.return_reason && !program.is_submitted && (
        <p className="mt-4 rounded-md bg-amber-50 p-3 text-sm text-amber-800">
          Motif du retour : {program.return_reason}
        </p>
      )}
      <div className="mt-5 flex flex-wrap justify-end gap-3">
        {editable && (
          <>
            <button type="button" onClick={() => action.mutate(() => updateTrainingProgram(caseId, metadata))} className="btn btn-secondary">Enregistrer le brouillon</button>
            <button type="button" onClick={() => action.mutate(() => submitTrainingProgram(caseId))} className="btn btn-primary px-5">Soumettre pour validation</button>
          </>
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
  selectedId,
  first,
  last,
  onSelect,
  onMove,
  onDelete,
}: {
  item: TrainingProgramItem;
  editable: boolean;
  selectedId: string | null;
  first: boolean;
  last: boolean;
  onSelect: (item: TrainingProgramItem) => void;
  onMove: (item: TrainingProgramItem, direction: "up" | "down") => void;
  onDelete: (item: TrainingProgramItem) => void;
}) {
  const selected = selectedId === item.id;
  return (
    <div>
      <div className={`flex items-center gap-2 rounded-lg border px-2.5 py-2 transition ${selected ? "border-violet-300 bg-violet-50 shadow-sm" : "border-transparent bg-white hover:border-slate-200 hover:bg-slate-50"}`}>
        <span aria-hidden="true" className="cursor-grab select-none text-slate-400">≡</span>
        <button type="button" aria-label={item.title} onClick={() => onSelect(item)} aria-pressed={selected} className="min-w-0 flex-1 text-left text-xs font-semibold text-slate-700 focus:outline-none focus:ring-2 focus:ring-violet-500">
          <span className="block truncate">{item.title}</span>
          <span className="mt-1 block text-[10px] font-normal text-slate-500">Théorie {formatMinutes(item.theory_total_minutes)} · Pratique {formatMinutes(item.practice_total_minutes)}</span>
          {conceptsFromContent(item.content).length > 0 && <span className="mt-1 block truncate text-[10px] font-normal text-slate-500">{conceptsFromContent(item.content).slice(0, 2).join(" · ")}</span>}
        </button>
        <span className="whitespace-nowrap text-[11px] font-medium text-slate-500">{formatMinutes(item.total_minutes)}</span>
        {editable && (
          <ActionMenu
            first={first}
            last={last}
            onUp={() => onMove(item, "up")}
            onDown={() => onMove(item, "down")}
            onDelete={() => onDelete(item)}
          />
        )}
      </div>
      <div className="ml-5">
        {item.children.map((child, index) => (
          <ProgramTreeItem
            key={child.id}
            item={child}
            editable={editable}
            selectedId={selectedId}
            first={index === 0}
            last={index === item.children.length - 1}
            onSelect={onSelect}
            onMove={onMove}
            onDelete={onDelete}
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
      <div className="flex items-center justify-between gap-3"><div><p className="text-xs font-bold uppercase tracking-wide text-violet-600">Éditeur du module</p><h3 className="mt-1 text-lg font-bold text-slate-900">{selected ? selected.title : "Nouveau module"}</h3></div><span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">{value.item_type === "MODULE" ? "Module" : "Sous-module"}</span></div>
      <div className="mt-4 grid gap-4">
        <TextField
          label="Titre du module"
          value={value.title}
          onChange={(title) => onChange({ ...value, title })}
        />
        <TextArea
          label="Concepts / contenus"
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
        <fieldset className="rounded-lg border border-slate-200 p-3">
          <legend className="px-1 text-xs font-semibold">Méthodes et moyens pédagogiques</legend>
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
        <div className="flex items-center justify-between rounded-lg bg-violet-50 px-4 py-3 text-sm"><span className="font-medium text-slate-600">Durée totale calculée</span><strong className="text-base text-violet-700">{formatMinutes(value.theory_minutes + value.practice_minutes)}</strong></div>
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
  const concepts = conceptsFromContent(item.content);
  return (
    <div>
      <h3 className="font-semibold">{item.title}</h3>
      {concepts.length > 0 && <ul className="mt-3 grid gap-1.5 text-sm text-slate-700">{concepts.map((concept, index) => <li key={`${concept}-${index}`} className="flex gap-2"><span className="text-violet-600">•</span>{concept}</li>)}</ul>}
      {item.methods.length > 0 && <div className="mt-4 flex flex-wrap gap-2">{item.methods.map((method) => <span key={method} className="rounded-full bg-slate-100 px-2.5 py-1 text-xs text-slate-700">{methodLabels[method]}</span>)}</div>}
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
    <div className="px-4 py-3 text-center">
      <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <strong className={`mt-1 block text-xl text-slate-900 ${className}`}>{formatMinutes(value)}</strong>
    </div>
  );
}

function ActionMenu({
  first,
  last,
  onUp,
  onDown,
  onDelete,
}: {
  first: boolean;
  last: boolean;
  onUp: () => void;
  onDown: () => void;
  onDelete: () => void;
}) {
  return (
    <details className="relative">
      <summary aria-label="Actions" className="grid size-7 cursor-pointer list-none place-items-center rounded-md text-base font-bold text-slate-500 hover:bg-slate-200 focus:outline-none focus:ring-2 focus:ring-violet-500">⋯</summary>
      <div className="absolute right-0 z-20 mt-1 min-w-32 rounded-lg border border-slate-200 bg-white p-1 text-xs shadow-lg">
        <button type="button" disabled={first} onClick={onUp} className="block w-full rounded px-3 py-2 text-left hover:bg-slate-50 disabled:opacity-40">Monter</button>
        <button type="button" disabled={last} onClick={onDown} className="block w-full rounded px-3 py-2 text-left hover:bg-slate-50 disabled:opacity-40">Descendre</button>
        <button type="button" onClick={onDelete} className="block w-full rounded px-3 py-2 text-left text-red-700 hover:bg-red-50">Supprimer</button>
      </div>
    </details>
  );
}

function EmptyEditor() {
  return <div className="grid min-h-[320px] place-items-center text-center"><div><span aria-hidden="true" className="mx-auto grid size-14 place-items-center rounded-2xl bg-violet-50 text-2xl text-violet-600">▤</span><p className="mt-4 max-w-sm text-sm font-medium text-slate-600">Sélectionnez un module pour afficher et modifier son contenu.</p></div></div>;
}

function ObjectivePreview({ value }: { value: string }) {
  const objectives = value.split(/\r?\n|;|•/).map((item) => item.trim()).filter(Boolean);
  if (objectives.length < 2) return null;
  return <div className="mt-4 rounded-lg bg-white p-3"><p className="text-xs font-bold uppercase tracking-wide text-slate-500">Aperçu des objectifs</p><ul className="mt-2 grid gap-1.5 text-sm text-slate-700 md:grid-cols-2">{objectives.map((objective, index) => <li key={`${objective}-${index}`} className="flex gap-2"><span className="text-violet-600">•</span><span>{objective}</span></li>)}</ul></div>;
}

function titlesSeemDifferent(theme: string, title: string): boolean {
  const normalize = (value: string) => value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("fr").replace(/[^a-z0-9]+/g, " ").trim();
  const normalizedTheme = normalize(theme);
  const normalizedTitle = normalize(title);
  if (!normalizedTheme || !normalizedTitle) return false;
  return !normalizedTitle.includes(normalizedTheme) && !normalizedTheme.includes(normalizedTitle);
}

function conceptsFromContent(content: string | null | undefined): string[] {
  if (!content) return [];
  return content.split(/[\r\n;]+/).map((value) => value.replace(/^[•\-\s]+/, "").trim()).filter(Boolean);
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
