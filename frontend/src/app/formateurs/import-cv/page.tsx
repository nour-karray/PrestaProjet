"use client";

import { useMutation } from "@tanstack/react-query";
import Link from "next/link";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { FileUploader, PageContainer } from "@/components/templates";
import { Icon, PageHeader, WorkflowStepper } from "@/components/ui";
import { TrainerForm } from "@/components/trainer-form";
import {
  extractTrainerCv,
  getTrainerCv,
  uploadTrainerCv,
  validateTrainerCv,
} from "@/features/trainers/api";
import { ApiError } from "@/lib/api";
import type { TrainerCv } from "@/types/trainer";

export default function ImportCvPage() {
  const [file, setFile] = useState<File | null>(null);
  const [cv, setCv] = useState<TrainerCv | null>(null);
  const [manual, setManual] = useState(false);
  const extraction = useMutation({
    mutationFn: (id: string) => extractTrainerCv(id),
    onSuccess: setCv,
    onError: async (_error, id) => {
      // The HTTP connection may close while the synchronous Ollama job finishes.
      // Always recover the durable server-side state instead of leaving the UI spinning.
      try {
        setCv(await getTrainerCv(id));
      } catch {
        // The mutation error displayed below remains the useful fallback.
      }
    },
  });
  const upload = useMutation({
    mutationFn: () => uploadTrainerCv(file!),
    onSuccess: (uploaded) => {
      setCv(uploaded);
      extraction.mutate(uploaded.id);
    },
  });
  const validation = useMutation({
    mutationFn: (values: Parameters<typeof validateTrainerCv>[1]) =>
      validateTrainerCv(cv!.id, values),
  });
  const error = upload.error ?? extraction.error ?? validation.error;
  const review = cv?.extraction_status === "REVIEW_REQUIRED";
  const aiUnavailable = review && Boolean(cv.extraction_error_code?.startsWith("LLM_"));
  const showForm = review || cv?.extraction_status === "AI_ANALYSIS_COMPLETED";
  const cvId = cv?.id;
  const reset = () => {
    setCv(null);
    setFile(null);
    setManual(false);
  };

  useEffect(() => {
    if (!cvId || !extraction.isPending) return;

    const interval = window.setInterval(async () => {
      try {
        const latest = await getTrainerCv(cvId);
        setCv(latest);
      } catch {
        // Polling is best-effort; the original request still owns the error state.
      }
    }, 3000);

    return () => window.clearInterval(interval);
  }, [cvId, extraction.isPending]);

  return <AppShell><PageContainer className="cv-import-page">
    <PageHeader eyebrow="Profil formateur" title="Importer et vérifier un CV"
      description="Chargez un PDF ou DOCX, puis vérifiez toujours les informations avant de créer le formateur." />
    <WorkflowStepper steps={["Fichier", "Vérification", "Validation"]}
      current={!cv ? 0 : validation.isSuccess ? 2 : 1} />

    {!cv && <section className="cv-upload-panel">
      <div className="cv-upload-copy"><span><Icon name="upload" /></span><div>
        <h2>Importer le CV du formateur</h2><p>PDF ou DOCX, 10 Mo maximum.</p>
      </div></div>
      <form onSubmit={(event) => { event.preventDefault(); upload.mutate(); }}>
        <FileUploader inputLabel="Choisir un CV" title={file ? file.name : "Déposez le CV ici"}
          description={file ? `${Math.ceil(file.size / 1024)} Ko — prêt à importer` : "Cliquez pour choisir un fichier"}
          accept=".pdf,.docx" onChange={(event) => setFile(event.target.files?.[0] ?? null)} />
        <button aria-label="Importer le CV" disabled={!file || upload.isPending}
          className="btn btn-primary cv-primary-action">
          {upload.isPending ? "Import en cours…" : "Importer et analyser"}<Icon name="arrow" />
        </button>
      </form>
    </section>}

    {cv && !validation.isSuccess && <section className="cv-workspace">
      <aside className="cv-file-summary">
        <span className="cv-file-icon">CV</span><h2>{cv.original_filename}</h2>
        <p>{Math.ceil(cv.file_size / 1024)} Ko</p>
        <button className="btn btn-ghost" type="button" onClick={reset}>Choisir un autre fichier</button>
      </aside>
      <div className="cv-analysis-panel">
        {extraction.isPending && !showForm && <div className="cv-analysis-empty" role="status">
          <span className="spinner" /><h2>Analyse du CV…</h2>
          <p>Extraction du texte puis vérification du service Ollama.</p>
        </div>}
        {showForm && <>
          <div className="cv-form-heading"><div><p className="page-eyebrow">Vérification humaine</p>
            <h2>Vérifier les informations du formateur</h2></div>
            <span className={`status-badge ${aiUnavailable ? "status-warning" : "status-success"}`}>
              {aiUnavailable ? "Saisie manuelle disponible" : "À vérifier"}
            </span>
          </div>
          <div className="cv-extraction-warning" role="status">
            <Icon name={aiUnavailable ? "alert" : "check"} /><div>
              <strong>{aiUnavailable
                ? "L’analyse automatique est indisponible, mais le fichier a bien été importé."
                : "Le CV est prêt pour votre vérification."}</strong>
              <p>✓ Fichier chargé<br />✓ Texte extrait<br />
                {aiUnavailable ? "✗ Analyse IA indisponible" : "✓ Analyse IA terminée"}<br />
                ○ Vérification manuelle</p>
              {cv.extraction_error && <p>{cv.extraction_error}</p>}
            </div>
            {aiUnavailable && <div>
              <button type="button" className="btn btn-secondary" disabled={extraction.isPending}
                onClick={() => extraction.mutate(cv.id)}>Réessayer l’analyse</button>
              <button type="button" className="btn btn-primary" onClick={() => setManual(true)}>
                Continuer manuellement</button>
            </div>}
          </div>
          {(!aiUnavailable || manual) && <TrainerForm initial={cv.parsed_json ?? {}}
            pending={validation.isPending} submitLabel="Valider et créer le formateur"
            onSubmit={(values) => validation.mutate(values)} />}
        </>}
      </div>
    </section>}

    {validation.isSuccess && <section className="cv-success" role="status">
      <span><Icon name="check" /></span><h2>Formateur créé avec succès</h2>
      <p>{validation.data.full_name} est disponible pour une affectation.</p>
      <Link href="/formateurs" className="btn btn-primary">Voir les formateurs</Link>
    </section>}
    {error && <p role="alert" className="cv-error">
      {error instanceof ApiError ? error.message : "L’opération a échoué."}
    </p>}
  </PageContainer></AppShell>;
}
