"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  downloadTrainingDocument,
  generateAllTrainingDocuments,
  generateTrainingDocument,
  getTrainingDocuments,
  initializeTrainingDocuments,
} from "@/features/training-documents/api";
import { ApiError } from "@/lib/api";
import type { TrainingCaseStatus } from "@/types/training-case";
import type { DocumentStatus, DocumentType, TrainingDocument } from "@/types/training-document";

const statusLabels: Record<DocumentStatus, string> = {
  PENDING: "En attente",
  GENERATED: "Généré",
  FAILED: "Échec",
};

export function TrainingDocumentsSection({
  caseId,
  caseStatus,
  onChanged,
}: {
  caseId: string;
  caseStatus: TrainingCaseStatus;
  onChanged: () => void;
}) {
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: ["training-documents", caseId],
    queryFn: () => getTrainingDocuments(caseId),
  });
  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ["training-documents", caseId] });
    onChanged();
  };
  const initialize = useMutation({
    mutationFn: () => initializeTrainingDocuments(caseId),
    onSuccess: refresh,
  });
  const generate = useMutation({
    mutationFn: (type: DocumentType) => generateTrainingDocument(caseId, type),
    onSuccess: refresh,
  });
  const generateAll = useMutation({
    mutationFn: () => generateAllTrainingDocuments(caseId),
    onSuccess: refresh,
  });
  const readonly = caseStatus === "TERMINE";
  const pending = initialize.isPending || generate.isPending || generateAll.isPending;
  const error = query.error ?? initialize.error ?? generate.error ?? generateAll.error;

  return (
    <section className="mt-6 rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="font-bold text-blue-800">10. Documents</h2>
          <p className="mt-1 text-xs text-slate-500">
            Cinq documents PDF obligatoires, générés et stockés localement.
          </p>
        </div>
        {caseStatus === "DOCUMENTS_GENERES" && (
          <span className="rounded bg-green-50 px-2 py-1 text-xs font-semibold text-green-700">
            Tous les documents sont générés
          </span>
        )}
      </div>

      {query.isPending ? (
        <p role="status" className="mt-5">Chargement des documents…</p>
      ) : (
        <div className="mt-5 overflow-x-auto">
          <table className="min-w-[720px] w-full text-left text-sm">
            <thead className="border-b text-xs text-slate-500">
              <tr>
                <th className="px-3 py-3">Type de document</th>
                <th className="px-3 py-3">Statut</th>
                <th className="px-3 py-3">Date</th>
                <th className="px-3 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {query.data?.map((item) => (
                <DocumentRow
                  key={item.id}
                  item={item}
                  readonly={readonly}
                  pending={pending}
                  onGenerate={() => generate.mutate(item.document_type)}
                  onDownload={() => downloadTrainingDocument(caseId, item.document_type)}
                />
              ))}
            </tbody>
          </table>
          {query.data?.length === 0 && (
            <p className="py-6 text-center text-sm text-slate-500">
              La phase Documents n’est pas encore initialisée.
            </p>
          )}
        </div>
      )}

      <div className="mt-5 flex flex-wrap justify-end gap-3">
        {!readonly && query.data?.length === 0 && (
          <button
            type="button"
            disabled={pending}
            onClick={() => initialize.mutate()}
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
          >
            {pending ? "Initialisation…" : "Initialiser les documents"}
          </button>
        )}
        {!readonly && Boolean(query.data?.length) && (
          <button
            type="button"
            disabled={pending}
            onClick={() => generateAll.mutate()}
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
          >
            {generateAll.isPending ? "Génération…" : "Générer tout"}
          </button>
        )}
        <button
          type="button"
          disabled
          title="Disponible dans une prochaine version"
          className="rounded-md border border-slate-200 px-4 py-2 text-sm text-slate-400"
        >
          Envoyer par email — prochaine version
        </button>
      </div>
      {error && (
        <p role="alert" className="mt-3 text-sm text-red-700">
          {error instanceof ApiError ? error.message : "L’opération documentaire a échoué."}
        </p>
      )}
    </section>
  );
}

function DocumentRow({
  item,
  readonly,
  pending,
  onGenerate,
  onDownload,
}: {
  item: TrainingDocument;
  readonly: boolean;
  pending: boolean;
  onGenerate: () => void;
  onDownload: () => void;
}) {
  const badge = item.status === "GENERATED"
    ? "bg-green-50 text-green-700"
    : item.status === "FAILED"
      ? "bg-red-50 text-red-700"
      : "bg-amber-50 text-amber-700";
  return (
    <tr>
      <td className="px-3 py-4 font-medium">{item.display_name}</td>
      <td className="px-3 py-4">
        <span className={`rounded px-2 py-1 text-xs font-semibold ${badge}`}>
          {statusLabels[item.status]}
        </span>
        {item.generation_error && <p className="mt-1 text-xs text-red-600">{item.generation_error}</p>}
      </td>
      <td className="px-3 py-4 text-slate-500">
        {item.generated_at ? new Date(item.generated_at).toLocaleDateString("fr-FR") : "—"}
      </td>
      <td className="px-3 py-4">
        <div className="flex justify-end gap-2">
          {!readonly && (
            <button
              type="button"
              disabled={pending}
              onClick={onGenerate}
              className="rounded border border-blue-200 px-3 py-1.5 text-xs font-semibold text-blue-700 disabled:opacity-50"
            >
              {item.status === "GENERATED" ? "Régénérer" : "Générer"}
            </button>
          )}
          <button
            type="button"
            disabled={item.status !== "GENERATED"}
            onClick={onDownload}
            className="rounded border border-slate-200 px-3 py-1.5 text-xs font-semibold disabled:text-slate-300"
          >
            Télécharger
          </button>
        </div>
      </td>
    </tr>
  );
}
