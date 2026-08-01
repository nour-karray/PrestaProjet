import { render, screen } from "@testing-library/react";
import type { AnchorHTMLAttributes } from "react";
import { describe, expect, it, vi } from "vitest";

import { AppHeader, AppSidebar } from "@/components/app-shell";
import { DataTableLayout, SuccessPageTemplate } from "@/components/templates";

vi.mock("next/link", () => ({
  default: ({ children, href, ...props }: AnchorHTMLAttributes<HTMLAnchorElement>) => <a href={String(href)} {...props}>{children}</a>,
}));

const administrator = {
  id: "admin-1",
  full_name: "Amina Ben Salah",
  email: "amina@formation.local",
  is_active: true,
  created_at: "2026-07-28T10:00:00Z",
  last_login_at: null,
};

describe("Templates Formation Center", () => {
  it("affiche la navigation, le sous-menu actif et le compte dynamique", () => {
    render(<AppSidebar pathname="/dossiers/nouveau" open collapsed={false} administrator={administrator} onClose={vi.fn()} onToggleCollapse={vi.fn()} />);
    expect(screen.getByText("Créer un dossier")).toBeInTheDocument();
    expect(screen.getByText("Amina Ben Salah")).toBeInTheDocument();
    expect(screen.queryByText("Rahma")).not.toBeInTheDocument();
  });

  it("affiche le header avec le rôle administrateur", () => {
    render(<AppHeader administrator={administrator} onMenu={vi.fn()} onLogout={vi.fn()} loggingOut={false} />);
    expect(screen.getByText("Amina Ben Salah")).toBeInTheDocument();
    expect(screen.getByText("Administrateur")).toBeInTheDocument();
  });

  it("compose un tableau et un succès sans données fictives", () => {
    render(<><DataTableLayout><table><tbody><tr><td>Donnée API</td></tr></tbody></table></DataTableLayout><SuccessPageTemplate title="DOS-1" description="Créé automatiquement" actions={<button>Continuer</button>} /></>);
    expect(screen.getByText("Donnée API")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Continuer" })).toBeInTheDocument();
  });
});
