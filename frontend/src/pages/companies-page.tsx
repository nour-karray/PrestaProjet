import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "@/router/navigation";
import { useState } from "react";

import { AppShell } from "@/components/app-shell";
import { Button, EmptyState, ErrorState, LoadingState, PageHeader, PrimaryLink, StatusBadge } from "@/components/ui";
import { archiveCompany, getCompanies } from "@/features/companies/api";
import { ApiError } from "@/lib/api";

export default function CompaniesPage() {
  const [search, setSearch] = useState("");
  const [city, setCity] = useState("");
  const [country, setCountry] = useState("");
  const [includeArchived, setIncludeArchived] = useState(false);
  const [page, setPage] = useState(1);
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: ["companies", search, city, country, includeArchived, page],
    queryFn: () => getCompanies({ search, city, country, includeArchived, page }),
    placeholderData: keepPreviousData,
  });
  const archiveMutation = useMutation({
    mutationFn: archiveCompany,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["companies"] }),
  });
  const resetPage = () => setPage(1);

  return (
    <AppShell>
      <PageHeader eyebrow="Répertoire clients" title="Entreprises" description="Gérez les entreprises clientes et leurs contacts principaux." action={<PrimaryLink href="/entreprises/nouvelle">Nouvelle entreprise</PrimaryLink>} />
      <div className="filter-panel company-filters">
        <input className="field" aria-label="Rechercher par nom" placeholder="Rechercher une entreprise…" value={search} onChange={(event) => { setSearch(event.target.value); resetPage(); }} />
        <input className="field" aria-label="Filtrer par ville" placeholder="Ville" value={city} onChange={(event) => { setCity(event.target.value); resetPage(); }} />
        <input className="field" aria-label="Filtrer par pays" placeholder="Pays" value={country} onChange={(event) => { setCountry(event.target.value); resetPage(); }} />
        <label className="archive-filter"><input type="checkbox" checked={includeArchived} onChange={(event) => { setIncludeArchived(event.target.checked); resetPage(); }} /> Inclure les archivées</label>
      </div>
      {query.isPending && <LoadingState label="Chargement des entreprises…" />}
      {query.isError && <ErrorState label={query.error instanceof ApiError ? query.error.message : "Impossible de charger les entreprises."} />}
      {query.data?.items.length === 0 && <EmptyState title="Aucune entreprise trouvée." description="Modifiez vos filtres ou créez une nouvelle entreprise." />}
      {query.data && query.data.items.length > 0 && <>
        <div className="data-panel"><table><thead><tr><th>Entreprise</th><th>Contact principal</th><th>Téléphone</th><th>Localisation</th><th>Statut</th><th>Actions</th></tr></thead><tbody>{query.data.items.map((company) => <tr key={company.id}>
          <td><Link className="company-name" href={`/entreprises/${company.id}`}><span>{company.name.slice(0, 2).toUpperCase()}</span><strong>{company.name}</strong></Link></td>
          <td><div className="contact-cell"><strong>{company.primary_contact?.full_name ?? "Non renseigné"}</strong><small>{company.primary_contact?.email ?? "Aucun email"}</small></div></td>
          <td>{company.primary_contact?.phone ?? "—"}</td><td>{[company.city, company.country].filter(Boolean).join(", ") || "—"}</td>
          <td><StatusBadge tone={company.is_archived ? "neutral" : "success"}>{company.is_archived ? "Archivée" : "Active"}</StatusBadge></td>
          <td><div className="row-actions"><Link href={`/entreprises/${company.id}`}>Consulter</Link>{!company.is_archived && <button onClick={() => archiveMutation.mutate(company.id)} disabled={archiveMutation.isPending}>Archiver</button>}</div></td>
        </tr>)}</tbody></table></div>
        <div className="pagination-bar"><Button disabled={page === 1} onClick={() => setPage((value) => value - 1)}>Précédent</Button><span>Page <strong>{page}</strong></span><Button disabled={page * query.data.page_size >= query.data.total} onClick={() => setPage((value) => value + 1)}>Suivant</Button></div>
      </>}
      <style>{`.company-filters{grid-template-columns:minmax(220px,1.4fr) 1fr 1fr auto}.archive-filter{display:flex;align-items:center;gap:8px;padding:0 8px;color:var(--muted);font-size:12px;white-space:nowrap}.company-name{display:flex;align-items:center;gap:10px;color:var(--text);text-decoration:none}.company-name span{width:34px;height:34px;display:grid;place-items:center;border-radius:10px;color:#5b3df5;background:#f0edff;font-size:10px;font-weight:800}.contact-cell{display:grid}.contact-cell small{margin-top:3px;color:var(--muted);font-size:10px}.row-actions{display:flex;gap:13px}.row-actions a,.row-actions button{border:0;color:#5b3df5;background:transparent;text-decoration:none;font-size:12px;font-weight:700;cursor:pointer}.row-actions button{color:#b42318}@media(max-width:850px){.company-filters{grid-template-columns:1fr 1fr}.data-panel table{min-width:850px}}@media(max-width:560px){.company-filters{grid-template-columns:1fr}}`}</style>
    </AppShell>
  );
}
