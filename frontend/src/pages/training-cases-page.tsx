import { keepPreviousData, useQuery } from "@tanstack/react-query";
import Link from "@/router/navigation";
import { useState } from "react";

import { AppShell } from "@/components/app-shell";
import { DataTableLayout, PageContainer } from "@/components/templates";
import { Button, EmptyState, ErrorState, LoadingState, PageHeader, PrimaryLink, StatusBadge } from "@/components/ui";
import { getCompanies } from "@/features/companies/api";
import { getTrainingCases } from "@/features/training-cases/api";
import { statusLabel } from "@/features/training-cases/status";
import { ApiError } from "@/lib/api";
import { trainingCaseStatuses, type TrainingCaseStatus } from "@/types/training-case";

const nextActions: Partial<Record<TrainingCaseStatus, string>> = {
  BROUILLON: "Compléter le dossier", DEMANDE_RECUE: "Lancer la recherche", RECHERCHE_FORMATEUR: "Choisir un formateur",
  FORMATEUR_PROPOSE: "Confirmer le formateur", FORMATEUR_ACCEPTE: "Compléter le besoin", BESOIN_A_COMPLETER: "Compléter le besoin",
  BESOIN_COMPLETE: "Créer le programme", PROGRAMME_EN_PREPARATION: "Finaliser le programme", PROGRAMME_A_VALIDER: "Valider le programme",
  PROGRAMME_VALIDE: "Calculer le prix", TARIFICATION_EN_PREPARATION: "Finaliser le prix", TARIFICATION_A_VALIDER: "Valider le prix",
  TARIFICATION_VALIDEE: "Préparer les documents", DOCUMENTS_A_GENERER: "Générer les documents", DOCUMENTS_GENERES: "Clôturer le dossier",
};

export default function TrainingCasesPage() {
  const [reference, setReference] = useState(""); const [companyId, setCompanyId] = useState(""); const [theme, setTheme] = useState("");
  const [status, setStatus] = useState(""); const [createdFrom, setCreatedFrom] = useState(""); const [createdTo, setCreatedTo] = useState("");
  const [includeArchived, setIncludeArchived] = useState(false); const [page, setPage] = useState(1);
  const companies = useQuery({ queryKey: ["companies", "case-filter"], queryFn: () => getCompanies({}) });
  const cases = useQuery({
    queryKey: ["training-cases", reference, companyId, theme, status, createdFrom, createdTo, includeArchived, page],
    queryFn: () => getTrainingCases({ reference, companyId, theme, status, createdFrom, createdTo, includeArchived, page }),
    placeholderData: keepPreviousData,
  });
  const resetPage = () => setPage(1);
  return <AppShell><PageContainer>
    <PageHeader eyebrow="Suivi opérationnel" title="Dossiers de formation" description="Suivez chaque dossier depuis la demande jusqu’à la génération des documents." action={<PrimaryLink href="/dossiers/nouveau">Nouveau dossier</PrimaryLink>} />
    <div className="filter-panel case-filters">
      <input className="field" aria-label="Référence" placeholder="Référence du dossier…" value={reference} onChange={(event) => { setReference(event.target.value); resetPage(); }} />
      <input className="field" aria-label="Thème" placeholder="Thème de formation…" value={theme} onChange={(event) => { setTheme(event.target.value); resetPage(); }} />
      <select className="field" aria-label="Entreprise" value={companyId} onChange={(event) => { setCompanyId(event.target.value); resetPage(); }}><option value="">Toutes les entreprises</option>{companies.data?.items.map((company) => <option key={company.id} value={company.id}>{company.name}</option>)}</select>
      <select className="field" aria-label="Statut" value={status} onChange={(event) => { setStatus(event.target.value); resetPage(); }}><option value="">Tous les statuts</option>{trainingCaseStatuses.map((item) => <option key={item} value={item}>{statusLabel(item)}</option>)}</select>
      <input className="field" aria-label="Créés depuis" type="date" value={createdFrom} onChange={(event) => { setCreatedFrom(event.target.value); resetPage(); }} />
      <input className="field" aria-label="Créés jusqu’au" type="date" value={createdTo} onChange={(event) => { setCreatedTo(event.target.value); resetPage(); }} />
      <label className="archive-filter"><input type="checkbox" checked={includeArchived} onChange={(event) => setIncludeArchived(event.target.checked)} /> Inclure les archivés</label>
    </div>
    {cases.isPending && <LoadingState label="Chargement des dossiers…" />}
    {cases.isError && <ErrorState label={cases.error instanceof ApiError ? cases.error.message : "Impossible de charger les dossiers."} />}
    {cases.data?.items.length === 0 && <EmptyState title="Aucun dossier trouvé" description="Modifiez vos filtres ou créez un nouveau dossier." />}
    {cases.data && cases.data.items.length > 0 && <DataTableLayout pagination={<div className="pagination-bar"><Button disabled={page === 1} onClick={() => setPage((value) => value - 1)}>Précédent</Button><span>Page <strong>{page}</strong></span><Button disabled={page * cases.data.page_size >= cases.data.total} onClick={() => setPage((value) => value + 1)}>Suivant</Button></div>}><table><thead><tr><th>Référence</th><th>Entreprise</th><th>Thème</th><th>Statut</th><th>Prochaine action</th><th>Dernière modification</th><th /></tr></thead><tbody>{cases.data.items.map((item) => <tr key={item.id}><td><Link className="reference" href={`/dossiers/${item.id}`}>{item.reference}</Link></td><td>{item.company.name}</td><td><span className="theme">{item.theme}</span></td><td><StatusBadge tone={item.status === "TERMINE" ? "success" : item.status === "ANNULE" || item.status === "ARCHIVE" ? "neutral" : "info"}>{statusLabel(item.status)}</StatusBadge></td><td><span className="next-action">{nextActions[item.status] ?? "—"}</span></td><td>{new Date(item.updated_at).toLocaleDateString("fr-FR")}</td><td><Link className="open-link" href={`/dossiers/${item.id}`}>Ouvrir →</Link></td></tr>)}</tbody></table></DataTableLayout>}
    <style>{`.case-filters{grid-template-columns:1.2fr 1.2fr 1fr 1fr auto}.archive-filter{display:flex;align-items:center;gap:8px;padding:0 5px;color:var(--muted);font-size:12px;white-space:nowrap}.reference{color:#3431a8;text-decoration:none;font-weight:800}.theme{display:block;max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.next-action{color:#344054;font-size:12px;font-weight:650}.open-link{color:#5b3df5;text-decoration:none;font-size:12px;font-weight:750}@media(max-width:1100px){.case-filters{grid-template-columns:1fr 1fr}.data-panel table{min-width:1000px}}@media(max-width:600px){.case-filters{grid-template-columns:1fr}}`}</style>
  </PageContainer></AppShell>;
}
