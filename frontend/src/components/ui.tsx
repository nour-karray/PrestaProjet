import Link from "@/router/navigation";
import type { ButtonHTMLAttributes, ReactNode } from "react";

export function Icon({
  name,
  className = "size-5",
}: {
  name: "home" | "folder" | "building" | "users" | "file" | "settings" | "search" | "logout" | "plus" | "arrow" | "check" | "alert" | "clock" | "menu" | "bell" | "book" | "help" | "edit" | "upload";
  className?: string;
}) {
  const paths = {
    home: <><path d="m3 11 9-8 9 8" /><path d="M5 10v10h14V10M9 20v-6h6v6" /></>,
    folder: <><path d="M3 6h6l2 2h10v11H3z" /><path d="M3 6v13" /></>,
    building: <><path d="M4 21V4h11v17M15 9h5v12M8 8h3M8 12h3M8 16h3M2 21h20" /></>,
    users: <><circle cx="9" cy="8" r="3" /><path d="M3 21v-2a6 6 0 0 1 12 0v2M16 4a3 3 0 0 1 0 6M17 14a5 5 0 0 1 4 5v2" /></>,
    file: <><path d="M6 2h8l4 4v16H6z" /><path d="M14 2v5h5M9 13h6M9 17h6" /></>,
    settings: <><circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1-2.8 2.8-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.6v.2h-4V21a1.7 1.7 0 0 0-1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1L4.2 17l.1-.1a1.7 1.7 0 0 0 .3-1.9A1.7 1.7 0 0 0 3 14H2.8v-4H3a1.7 1.7 0 0 0 1.6-1 1.7 1.7 0 0 0-.3-1.9L4.2 7 7 4.2l.1.1A1.7 1.7 0 0 0 9 4.6 1.7 1.7 0 0 0 10 3V2.8h4V3a1.7 1.7 0 0 0 1 1.6 1.7 1.7 0 0 0 1.9-.3l.1-.1L19.8 7l-.1.1a1.7 1.7 0 0 0-.3 1.9 1.7 1.7 0 0 0 1.6 1h.2v4H21a1.7 1.7 0 0 0-1.6 1Z" /></>,
    search: <><circle cx="11" cy="11" r="7" /><path d="m20 20-4-4" /></>,
    logout: <><path d="M10 17l5-5-5-5M15 12H3M14 3h7v18h-7" /></>,
    plus: <path d="M12 5v14M5 12h14" />,
    arrow: <path d="m9 18 6-6-6-6" />,
    check: <path d="m5 12 4 4L19 6" />,
    alert: <><path d="M12 3 2 21h20z" /><path d="M12 9v5M12 18h.01" /></>,
    clock: <><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></>,
    menu: <><path d="M4 7h16M4 12h16M4 17h16" /></>,
    bell: <><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4" /></>,
    book: <><path d="M4 4h6a3 3 0 0 1 3 3v13a3 3 0 0 0-3-3H4z" /><path d="M20 4h-6a3 3 0 0 0-3 3v13a3 3 0 0 1 3-3h6z" /></>,
    help: <><circle cx="12" cy="12" r="9" /><path d="M9.8 9a2.4 2.4 0 1 1 3.8 1.9c-1 .7-1.6 1.2-1.6 2.6M12 17h.01" /></>,
    edit: <><path d="M4 20h4L19 9l-4-4L4 16z" /><path d="m13.5 6.5 4 4" /></>,
    upload: <><path d="M12 16V4M7 9l5-5 5 5" /><path d="M4 15v5h16v-5" /></>,
  };
  return <svg aria-hidden="true" className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">{paths[name]}</svg>;
}

export function PageHeader({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return <header className="page-header"><div>{eyebrow && <p className="page-eyebrow">{eyebrow}</p>}<h1>{title}</h1>{description && <p>{description}</p>}</div>{action}</header>;
}

export function PrimaryLink({ href, children }: { href: string; children: ReactNode }) {
  return <Link href={href} className="btn-primary"><Icon name="plus" className="size-4" />{children}</Link>;
}

export function Button({
  variant = "secondary",
  className = "",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "secondary" | "danger" | "ghost" }) {
  return <button {...props} className={`btn btn-${variant} ${className}`} />;
}

export function StatusBadge({ children, tone = "info" }: { children: ReactNode; tone?: "success" | "warning" | "danger" | "info" | "neutral" }) {
  return <span className={`status-badge status-${tone}`}>{children}</span>;
}

export function LoadingState({ label = "Chargement…" }: { label?: string }) {
  return <div className="state-card" role="status"><span className="spinner" /><p>{label}</p></div>;
}

export function ErrorState({ label }: { label: string }) {
  return <div className="state-card state-error" role="alert"><Icon name="alert" /><p>{label}</p></div>;
}

export function FeedbackToast({ tone = "success", children }: { tone?: "success" | "error"; children: ReactNode }) {
  return <p className={tone === "success" ? "toast-success" : "toast-error"} role={tone === "success" ? "status" : "alert"}>{children}</p>;
}

export function EmptyState({ title, description }: { title: string; description?: string }) {
  return <div className="state-card"><span className="state-icon"><Icon name="folder" /></span><strong>{title}</strong>{description && <p>{description}</p>}</div>;
}

export type WorkflowStep = {
  label: string;
  state?: "completed" | "current" | "available" | "locked";
  reason?: string;
  href?: string;
};

export function WorkflowStepper({ steps, current }: { steps: Array<string | WorkflowStep>; current?: number }) {
  const normalized = steps.map((step, index): WorkflowStep =>
    typeof step === "string"
      ? { label: step, state: index < (current ?? 0) ? "completed" : index === (current ?? 0) ? "current" : "locked" }
      : step,
  );
  const activeIndex = normalized.findIndex((step) => step.state === "current");
  return <section className="workflow-progress">
    <p className="workflow-count">Étape {Math.max(1, activeIndex + 1)} sur {normalized.length}</p>
    <ol className="workflow-stepper" aria-label="Progression du dossier">{normalized.map((step, index) => {
      const content = <><span>{step.state === "completed" ? <Icon name="check" className="size-4" /> : step.state === "locked" ? "×" : index + 1}</span><strong>{step.label}</strong>{step.reason && <small>{step.reason}</small>}</>;
      return <li key={step.label} className={step.state} title={step.reason}>
        {step.href && step.state !== "locked" ? <Link href={step.href}>{content}</Link> : <div aria-disabled={step.state === "locked"}>{content}</div>}
      </li>;
    })}</ol>
  </section>;
}

export function WorkflowActionBar({
  back,
  status,
  prerequisite,
  primary,
}: {
  back?: ReactNode;
  status?: ReactNode;
  prerequisite?: string;
  primary: ReactNode;
}) {
  return <div className="workflow-action-bar">
    <div>{back}</div>
    <div className="workflow-action-state">{status}{prerequisite && <p>{prerequisite}</p>}</div>
    <div>{primary}</div>
  </div>;
}
