"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { AppShell } from "@/components/app-shell";
import { EmptyState, ErrorState, Icon, LoadingState, PageHeader, PrimaryLink, StatusBadge } from "@/components/ui";
import { getDashboard } from "@/features/training-cases/api";
import { statusLabel } from "@/features/training-cases/status";
import type { TrainingCaseStatus } from "@/types/training-case";

const nextActions: Partial<Record<TrainingCaseStatus, string>> = {
  BROUILLON: "Compléter le dossier",
  DEMANDE_RECUE: "Lancer la recherche",
  RECHERCHE_FORMATEUR: "Choisir un formateur",
  FORMATEUR_PROPOSE: "Confirmer le formateur",
  FORMATEUR_ACCEPTE: "Compléter le besoin",
  BESOIN_A_COMPLETER: "Compléter le besoin",
  BESOIN_COMPLETE: "Créer le programme",
  PROGRAMME_EN_PREPARATION: "Finaliser le programme",
  PROGRAMME_A_VALIDER: "Valider le programme",
  PROGRAMME_VALIDE: "Calculer le prix",
  TARIFICATION_EN_PREPARATION: "Finaliser le prix",
  TARIFICATION_A_VALIDER: "Valider le prix",
  TARIFICATION_VALIDEE: "Préparer les documents",
  DOCUMENTS_A_GENERER: "Générer les documents",
  DOCUMENTS_GENERES: "Clôturer le dossier",
};

export default function DashboardPage() {
  const query = useQuery({ queryKey: ["dashboard"], queryFn: getDashboard });
  if (query.isPending) return <AppShell><LoadingState label="Chargement du tableau de bord…" /></AppShell>;
  if (query.isError) return <AppShell><ErrorState label="Impossible de charger le tableau de bord." /></AppShell>;
  const cards = [
    { label: "Dossiers actifs", value: query.data.active_count, icon: "folder" as const, tone: "violet" },
    { label: "Dossiers récents", value: query.data.recent_cases.length, icon: "clock" as const, tone: "blue" },
    { label: "Dossiers annulés", value: query.data.cancelled_count, icon: "alert" as const, tone: "amber" },
    { label: "Dossiers archivés", value: query.data.archived_count, icon: "check" as const, tone: "green" },
  ];
  return (
    <AppShell>
      <PageHeader eyebrow="Vue d’ensemble" title="Bonjour, Administrateur 👋" description="Votre nom connecté est affiché dans l’en-tête. Voici les dossiers qui demandent votre attention." action={<PrimaryLink href="/dossiers/nouveau">Nouveau dossier</PrimaryLink>} />
      <div className="stat-grid">
        {cards.map((card) => <article className="stat-card" key={card.label}><span className={`stat-icon stat-${card.tone}`}><Icon name={card.icon} /></span><div><p>{card.label}</p><strong>{card.value}</strong><Link href="/dossiers">Voir les dossiers <span>→</span></Link></div></article>)}
      </div>
      <div className="dashboard-grid">
        <section className="panel action-panel">
          <div className="section-heading"><div><h2>Mes prochaines actions</h2><p>Priorités calculées à partir des derniers dossiers</p></div><Link href="/dossiers">Tout afficher</Link></div>
          {query.data.recent_cases.length === 0 ? <EmptyState title="Aucune action en attente" description="Créez un premier dossier pour commencer." /> : (
            <div className="action-list">{query.data.recent_cases.map((item) => <article key={item.id}><span className="action-dot" /><div className="action-main"><Link href={`/dossiers/${item.id}`}>{item.reference}</Link><p>{item.company.name} · {item.theme}</p></div><div className="action-next"><span>Prochaine action</span><strong>{nextActions[item.status] || statusLabel(item.status)}</strong></div><Link className="open-action" href={`/dossiers/${item.id}`} aria-label={`Ouvrir ${item.reference}`}><Icon name="arrow" /></Link></article>)}</div>
          )}
        </section>
        <aside className="panel quick-panel">
          <div className="section-heading"><div><h2>Actions rapides</h2><p>Accès directs</p></div></div>
          <Link href="/entreprises/nouvelle"><span><Icon name="building" /></span><div><strong>Nouvelle entreprise</strong><small>Ajouter un client</small></div><Icon name="arrow" /></Link>
          <Link href="/formateurs/import-cv"><span><Icon name="file" /></span><div><strong>Importer un CV</strong><small>Analyser un profil</small></div><Icon name="arrow" /></Link>
          <Link href="/dossiers"><span><Icon name="folder" /></span><div><strong>Voir les dossiers</strong><small>Suivre les formations</small></div><Icon name="arrow" /></Link>
        </aside>
      </div>
      <section className="panel recent-panel">
        <div className="section-heading"><div><h2>Dossiers récents</h2><p>Dernières modifications enregistrées</p></div></div>
        {query.data.recent_cases.length > 0 && <div className="table-scroll"><table><thead><tr><th>Référence</th><th>Entreprise</th><th>Formation</th><th>Statut</th><th>Mise à jour</th><th /></tr></thead><tbody>{query.data.recent_cases.map((item) => <tr key={item.id}><td><Link href={`/dossiers/${item.id}`}>{item.reference}</Link></td><td>{item.company.name}</td><td>{item.theme}</td><td><StatusBadge tone={item.status === "ANNULE" ? "danger" : item.status === "TERMINE" ? "success" : "info"}>{statusLabel(item.status)}</StatusBadge></td><td>{new Date(item.updated_at).toLocaleDateString("fr-FR")}</td><td><Link className="row-link" href={`/dossiers/${item.id}`}>Ouvrir</Link></td></tr>)}</tbody></table></div>}
      </section>
      <style>{`
        .stat-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px}.stat-card{display:flex;align-items:center;gap:15px;padding:20px;border:1px solid var(--border);border-radius:15px;background:white;box-shadow:var(--shadow)}.stat-icon{width:48px;height:48px;display:grid;place-items:center;flex:none;border-radius:13px}.stat-icon :global(svg){width:22px}.stat-violet{color:#5b3df5;background:#f0edff}.stat-blue{color:#2864f0;background:#edf4ff}.stat-amber{color:#d97706;background:#fff7e7}.stat-green{color:#16835a;background:#eafaf2}.stat-card p{margin:0;color:var(--muted);font-size:12px;font-weight:650}.stat-card strong{display:block;margin:3px 0;font-size:25px}.stat-card a{color:#5b3df5;text-decoration:none;font-size:11px;font-weight:700}.dashboard-grid{display:grid;grid-template-columns:minmax(0,1.8fr) minmax(260px,.7fr);gap:18px;margin-top:18px}.action-panel,.quick-panel,.recent-panel{padding:22px}.section-heading{display:flex;align-items:center;justify-content:space-between;margin-bottom:16px}.section-heading h2{margin:0;font-size:17px}.section-heading p{margin:4px 0 0;color:var(--muted);font-size:11px}.section-heading>a{color:#5b3df5;text-decoration:none;font-size:12px;font-weight:700}.action-list{display:grid}.action-list article{display:flex;align-items:center;gap:13px;padding:15px 0;border-top:1px solid #f0f1f4}.action-list article:first-child{border-top:0}.action-dot{width:9px;height:9px;flex:none;border:3px solid #d8d2ff;border-radius:50%;background:#5b3df5}.action-main{min-width:0;flex:1}.action-main a{color:#202551;text-decoration:none;font-weight:800}.action-main p{overflow:hidden;margin:3px 0 0;color:var(--muted);font-size:11px;text-overflow:ellipsis;white-space:nowrap}.action-next{display:grid;width:175px}.action-next span{color:#98a2b3;font-size:10px}.action-next strong{margin-top:2px;font-size:12px}.open-action{width:32px;height:32px;display:grid;place-items:center;border-radius:9px;color:#5b3df5;background:#f0edff}.open-action :global(svg){width:16px}.quick-panel>a{display:flex;align-items:center;gap:11px;padding:13px 0;border-top:1px solid #f0f1f4;color:inherit;text-decoration:none}.quick-panel>a>span{width:38px;height:38px;display:grid;place-items:center;border-radius:10px;color:#5b3df5;background:#f0edff}.quick-panel>a>span :global(svg){width:18px}.quick-panel>a>div{display:grid;flex:1}.quick-panel>a strong{font-size:12px}.quick-panel>a small{margin-top:3px;color:var(--muted);font-size:10px}.quick-panel>a>:global(svg){width:15px;color:#98a2b3}.recent-panel{margin-top:18px}.table-scroll{overflow:auto}.recent-panel table{width:100%;border-collapse:collapse}.recent-panel th,.recent-panel td{padding:13px;text-align:left;border-top:1px solid #f0f1f4;font-size:12px}.recent-panel th{color:var(--muted);background:#fafbff;font-size:10px}.recent-panel td>a{color:#272c64;font-weight:800;text-decoration:none}.recent-panel .row-link{color:#5b3df5;font-size:11px}@media(max-width:1150px){.stat-grid{grid-template-columns:repeat(2,1fr)}.dashboard-grid{grid-template-columns:1fr}}@media(max-width:600px){.stat-grid{grid-template-columns:1fr}.action-next{display:none}.recent-panel{padding:16px}.recent-panel table{min-width:680px}}
      `}</style>
    </AppShell>
  );
}
