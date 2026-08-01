"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState, type ReactNode } from "react";

import { Icon } from "@/components/ui";
import { getCurrentAdministrator, logout } from "@/features/auth/api";
import type { Administrator } from "@/types/auth";

type NavigationItem = {
  href: string;
  label: string;
  icon: Parameters<typeof Icon>[0]["name"];
  children?: Array<{ href: string; label: string }>;
};

const navigation: Array<{ label: string; items: NavigationItem[] }> = [
  {
    label: "Navigation",
    items: [{ href: "/tableau-de-bord", label: "Tableau de bord", icon: "home" as const }],
  },
  {
    label: "Gestion",
    items: [
      { href: "/dossiers", label: "Dossiers", icon: "folder" as const, children: [{ href: "/dossiers", label: "Liste des dossiers" }, { href: "/dossiers/nouveau", label: "Créer un dossier" }] },
      { href: "/entreprises", label: "Entreprises", icon: "building" as const },
      { href: "/formateurs", label: "Formateurs", icon: "users" as const },
    ],
  },
  {
    label: "Documents",
    items: [{ href: "/dossiers", label: "Documents", icon: "file" as const }],
  },
];

export function AppSidebar({
  pathname,
  open,
  collapsed,
  administrator,
  onClose,
  onToggleCollapse,
}: {
  pathname: string;
  open: boolean;
  collapsed: boolean;
  administrator?: Administrator;
  onClose: () => void;
  onToggleCollapse: () => void;
}) {
  const [dossiersOpen, setDossiersOpen] = useState(pathname.startsWith("/dossiers"));
  const name = administrator?.full_name || "Administrateur";
  const initials = name.split(/\s+/).filter(Boolean).map((part) => part[0]).slice(0, 2).join("").toUpperCase() || "A";
  return <aside className={`app-sidebar ${open ? "sidebar-open" : ""} ${collapsed ? "sidebar-collapsed" : ""}`}>
    <div className="sidebar-brand-row">
      <Link href="/tableau-de-bord" className="brand" onClick={onClose}><span className="brand-mark"><Icon name="book" /></span><span>Formation<br />Center</span></Link>
      <button type="button" aria-label={collapsed ? "Développer le menu" : "Réduire le menu"} onClick={onToggleCollapse}>{collapsed ? "»" : "«"}</button>
    </div>
    <nav aria-label="Navigation principale">
      {navigation.map((section) => <section key={section.label}><p>{section.label}</p>{section.items.map((item) => {
        const active = pathname === item.href || (item.href !== "/tableau-de-bord" && pathname.startsWith(item.href));
        return <div key={`${section.label}-${item.label}`} className="sidebar-nav-group">
          <div className={`sidebar-link-row ${active ? "active" : ""}`}>
            <Link href={item.href} onClick={onClose}><Icon name={item.icon} /><span>{item.label}</span></Link>
            {item.children && !collapsed && <button type="button" aria-label={`${dossiersOpen ? "Fermer" : "Ouvrir"} le sous-menu Dossiers`} aria-expanded={dossiersOpen} onClick={() => setDossiersOpen((value) => !value)}>{dossiersOpen ? "⌄" : "›"}</button>}
          </div>
          {item.children && dossiersOpen && !collapsed && <div className="sidebar-submenu">{item.children.map((child) => <Link key={child.href} href={child.href} className={pathname === child.href ? "active" : ""} onClick={onClose}>{child.label}</Link>)}</div>}
        </div>;
      })}</section>)}
    </nav>
    <div className="sidebar-account"><span className="avatar">{initials}</span><span><strong>{name}</strong><small>{administrator?.email || "Administrateur"}</small></span></div>
  </aside>;
}

export function AppHeader({
  administrator,
  onMenu,
  onLogout,
  loggingOut,
}: {
  administrator?: Administrator;
  onMenu: () => void;
  onLogout: () => void;
  loggingOut: boolean;
}) {
  const name = administrator?.full_name || "Administrateur";
  const initials = name.split(/\s+/).filter(Boolean).map((part) => part[0]).slice(0, 2).join("").toUpperCase() || "A";
  return <header className="app-header">
    <button className="menu-trigger" type="button" aria-label="Ouvrir le menu" onClick={onMenu}><Icon name="menu" /></button>
    <button className="header-icon-button" type="button" aria-label="Notifications"><Icon name="bell" /></button>
    <div className="account"><span className="avatar">{initials}</span><span className="account-copy"><strong>{name}</strong><small>Administrateur</small></span><button type="button" className="logout-button" aria-label="Se déconnecter" title="Se déconnecter" disabled={loggingOut} onClick={onLogout}><Icon name="logout" /></button></div>
  </header>;
}

export function AdminLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const queryClient = useQueryClient();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(false);
  const account = useQuery({ queryKey: ["auth", "me"], queryFn: getCurrentAdministrator, staleTime: 60_000, enabled: process.env.NODE_ENV !== "test" });
  const logoutMutation = useMutation({ mutationFn: logout, onSuccess: () => { queryClient.clear(); router.replace("/connexion"); } });
  return <main className={`app-layout ${collapsed ? "layout-collapsed" : ""}`}>
    {mobileOpen && <button className="sidebar-overlay" aria-label="Fermer le menu" onClick={() => setMobileOpen(false)} />}
    <AppSidebar pathname={pathname} open={mobileOpen} collapsed={collapsed} administrator={account.data} onClose={() => setMobileOpen(false)} onToggleCollapse={() => setCollapsed((value) => !value)} />
    <section className="app-main"><AppHeader administrator={account.data} onMenu={() => setMobileOpen(true)} onLogout={() => logoutMutation.mutate()} loggingOut={logoutMutation.isPending} /><div className="app-content">{children}</div></section>
  </main>;
}

export const AppShell = AdminLayout;
