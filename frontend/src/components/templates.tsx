"use client";

import type { InputHTMLAttributes, ReactNode } from "react";

import { Icon } from "@/components/ui";

export function AuthLayout({ children, visual }: { children: ReactNode; visual: ReactNode }) {
  return <main className="auth-layout"><section className="auth-card"><div className="auth-form-panel">{children}</div><aside className="auth-visual-panel">{visual}</aside></section></main>;
}

export function PageContainer({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <div className={`page-container ${className}`}>{children}</div>;
}

export function FormPageLayout({ children }: { children: ReactNode }) {
  return <section className="form-page-layout">{children}</section>;
}

export function DetailPageLayout({ main, aside }: { main: ReactNode; aside?: ReactNode }) {
  return <div className={`detail-page-layout ${aside ? "has-aside" : ""}`}><div>{main}</div>{aside && <aside>{aside}</aside>}</div>;
}

export function DataTableLayout({ filters, children, pagination }: { filters?: ReactNode; children: ReactNode; pagination?: ReactNode }) {
  return <section className="data-table-layout">{filters && <div className="data-table-filters">{filters}</div>}<div className="data-table-scroll">{children}</div>{pagination && <footer>{pagination}</footer>}</section>;
}

export function StickyActionBar({ secondary, primary, status }: { secondary?: ReactNode; primary: ReactNode; status?: ReactNode }) {
  return <div className="sticky-action-template"><div>{secondary}</div><div className="sticky-action-status">{status}</div><div>{primary}</div></div>;
}

export function SuccessPageTemplate({
  eyebrow,
  title,
  description,
  details,
  actions,
}: {
  eyebrow?: string;
  title: string;
  description: string;
  details?: ReactNode;
  actions: ReactNode;
}) {
  return <section className="success-page-template" role="status"><span className="success-icon"><Icon name="check" /></span><div>{eyebrow && <p className="page-eyebrow">{eyebrow}</p>}<h1>{title}</h1><p>{description}</p>{details}</div><div className="success-actions">{actions}</div></section>;
}

export function Combobox({
  label,
  required,
  expanded,
  children,
  className = "",
  ...inputProps
}: InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  required?: boolean;
  expanded: boolean;
  children?: ReactNode;
}) {
  return <label className={`template-combobox ${className}`}><span>{label}{required && <em> *</em>}</span><div className="template-combobox-anchor"><Icon name="search" /><input {...inputProps} role="combobox" aria-controls={inputProps["aria-controls"] ?? "combobox-options"} aria-expanded={expanded} aria-label={label} autoComplete="off" /></div>{children}</label>;
}

export function FileUploader({ title, description, accept, onChange, inputLabel = "Choisir un fichier" }: { title: string; description: string; accept?: string; onChange?: InputHTMLAttributes<HTMLInputElement>["onChange"]; inputLabel?: string }) {
  return <label className="file-uploader"><span className="file-uploader-icon"><Icon name="file" /></span><strong>{title}</strong><p>{description}</p><input aria-label={inputLabel} type="file" accept={accept} onChange={onChange} /></label>;
}
