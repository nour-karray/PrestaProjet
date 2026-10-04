import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useEffect, useMemo, useRef, useState } from "react";
import { useForm, useWatch } from "react-hook-form";
import { z } from "zod";

import { WorkflowActionBar } from "@/components/ui";
import { createCompany, createContact, getCompanies, getCompany } from "@/features/companies/api";
import { getTrainingCatalog } from "@/features/training-catalog/api";
import { ApiError } from "@/lib/api";
import type { CompanyListItem, Contact } from "@/types/company";
import type { TrainingCaseInput } from "@/types/training-case";

const schema = z.object({
  company_id: z.string().min(1, "L’entreprise est obligatoire."),
  primary_contact_id: z.string(),
  theme: z.string().trim().min(1, "Le thème est obligatoire."),
  description: z.string().trim().max(1000),
});
type FormValues = z.infer<typeof schema>;

function useOutsideClose(ref: React.RefObject<HTMLElement | null>, close: () => void) {
  useEffect(() => {
    const handler = (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) close();
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [close, ref]);
}

export function TrainingCaseForm({
  companies,
  initial,
  pending,
  submitLabel = "Créer le dossier et continuer",
  onSubmit,
}: {
  companies: CompanyListItem[];
  initial?: Partial<TrainingCaseInput>;
  pending: boolean;
  submitLabel?: string;
  onSubmit: (values: TrainingCaseInput, mode?: "continue" | "draft") => void;
}) {
  const initialCompany = companies.find((item) => item.id === initial?.company_id) ?? null;
  const [selectedCompany, setSelectedCompany] = useState<CompanyListItem | null>(initialCompany);
  const [companyText, setCompanyText] = useState(initialCompany?.name ?? "");
  const [debouncedCompanyText, setDebouncedCompanyText] = useState("");
  const [companyOpen, setCompanyOpen] = useState(false);
  const [companyActive, setCompanyActive] = useState(-1);
  const [contactOpen, setContactOpen] = useState(false);
  const [contactSearch, setContactSearch] = useState("");
  const [contactModal, setContactModal] = useState(false);
  const [contactDraft, setContactDraft] = useState({ full_name: "", phone: "", email: "" });
  const [feedback, setFeedback] = useState<string | null>(null);
  const companyRef = useRef<HTMLDivElement>(null);
  const contactRef = useRef<HTMLDivElement>(null);
  const { register, handleSubmit, setValue, control, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      company_id: initial?.company_id ?? "",
      primary_contact_id: initial?.primary_contact_id ?? "",
      theme: initial?.theme ?? "",
      description: initial?.description ?? "",
    },
  });
  const companyId = useWatch({ control, name: "company_id" });
  const contactId = useWatch({ control, name: "primary_contact_id" });
  const theme = useWatch({ control, name: "theme" });
  const description = useWatch({ control, name: "description" });
  const formReady = Boolean(companyId && theme.trim());
  const trainingCatalog = useQuery({ queryKey: ["training-catalog"], queryFn: getTrainingCatalog });
  const catalogByCategory = useMemo(() => {
    const grouped = new Map<string, string[]>();
    for (const item of Array.isArray(trainingCatalog.data) ? trainingCatalog.data : []) {
      if (!item.is_active) continue;
      grouped.set(item.category, [...(grouped.get(item.category) ?? []), item.title]);
    }
    return [...grouped.entries()];
  }, [trainingCatalog.data]);
  const catalogIsFamilyList = useMemo(
    () => catalogByCategory.every(([category, items]) => items.length === 1 && items[0] === category),
    [catalogByCategory],
  );

  useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedCompanyText(companyText.trim()), 300);
    return () => window.clearTimeout(timer);
  }, [companyText]);
  const companySearch = useQuery({
    queryKey: ["companies", "combobox", debouncedCompanyText],
    queryFn: () => getCompanies({ search: debouncedCompanyText, page: 1, pageSize: 8 }),
    // On ouvre d'abord le catalogue des sociétés existantes ; la saisie ne
    // sert ensuite qu'à filtrer cette même liste.
    enabled: companyOpen && !selectedCompany && debouncedCompanyText.length > 0,
  });
  const companyResults = (debouncedCompanyText ? companySearch.data?.items ?? [] : companies).slice(0, 8);
  const companyExact = companyResults.some((item) => item.name.trim().toLocaleLowerCase("fr") === companyText.trim().toLocaleLowerCase("fr"));
  const companyQuery = useQuery({
    queryKey: ["company-contacts", companyId],
    queryFn: () => getCompany(companyId),
    enabled: Boolean(companyId),
  });
  const contacts = useMemo(() => [...(companyQuery.data?.contacts ?? [])].sort((a, b) => Number(b.is_primary) - Number(a.is_primary)), [companyQuery.data?.contacts]);
  const visibleContacts = contacts.filter((contact) => [contact.full_name, contact.email, contact.phone].filter(Boolean).join(" ").toLocaleLowerCase("fr").includes(contactSearch.trim().toLocaleLowerCase("fr"))).slice(0, 8);
  const selectedContact = contacts.find((contact) => contact.id === contactId);

  useOutsideClose(companyRef, () => setCompanyOpen(false));
  useOutsideClose(contactRef, () => setContactOpen(false));

  const selectCompany = (company: CompanyListItem) => {
    setSelectedCompany(company);
    setCompanyText(company.name);
    setValue("company_id", company.id, { shouldValidate: true });
    setValue("primary_contact_id", "");
    setCompanyOpen(false);
    setFeedback(`Entreprise « ${company.name} » sélectionnée.`);
  };
  const companyCreation = useMutation({
    mutationFn: () => createCompany({ name: companyText.trim() }),
    onSuccess: (company) => {
      selectCompany({ ...company, primary_contact: null });
      setFeedback(`Entreprise « ${company.name} » créée et sélectionnée.`);
    },
  });
  const contactCreation = useMutation({
    mutationFn: () => createContact(companyId, { ...contactDraft, is_primary: contacts.length === 0 }),
    onSuccess: (contact: Contact) => {
      setValue("primary_contact_id", contact.id);
      setContactModal(false);
      setContactDraft({ full_name: "", phone: "", email: "" });
      setFeedback(`${contact.full_name} a été ajouté et sélectionné.`);
      companyQuery.refetch();
    },
  });
  const submit = (mode: "continue" | "draft") => handleSubmit((values) => onSubmit({
    company_id: values.company_id,
    primary_contact_id: values.primary_contact_id || null,
    theme: values.theme.trim(),
    description: values.description.trim() || undefined,
  }, mode));
  const companyKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Escape") return setCompanyOpen(false);
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      setCompanyOpen(true);
      setCompanyActive((current) => event.key === "ArrowDown" ? Math.min(current + 1, companyResults.length - 1) : Math.max(current - 1, 0));
    }
    if (event.key === "Enter" && companyActive >= 0 && companyResults[companyActive]) {
      event.preventDefault();
      selectCompany(companyResults[companyActive]);
    }
  };
  const actionError = companyCreation.error ?? contactCreation.error;

  return <form onSubmit={submit("continue")} className="case-create-form case-create-form-simple" noValidate>
    {feedback && <p className="toast-success" role="status">{feedback}</p>}
    <div className="case-company-field" ref={companyRef}>
      <label htmlFor="company-combobox">Entreprise <em>*</em></label>
      {!selectedCompany ? <>
        <div className="combobox-anchor">
          <span>⌕</span>
          <input id="company-combobox" role="combobox" aria-expanded={companyOpen} aria-controls="company-options" aria-activedescendant={companyActive >= 0 ? `company-option-${companyActive}` : undefined} aria-autocomplete="list" value={companyText} onFocus={() => setCompanyOpen(true)} onChange={(event) => { setCompanyText(event.target.value); setCompanyOpen(true); setCompanyActive(-1); }} onKeyDown={companyKeyDown} placeholder="Choisir ou rechercher une société…" className="field" autoComplete="off" />
        </div>
        {companyOpen && <div className="combobox-menu" id="company-options" role="listbox">
          {!companyText.trim() && <p>Sociétés déjà enregistrées</p>}
          {companySearch.isFetching && <p role="status">Recherche en cours…</p>}
          {companyResults.map((company, index) => <button id={`company-option-${index}`} role="option" aria-selected={companyActive === index} type="button" key={company.id} onMouseDown={(event) => event.preventDefault()} onClick={() => selectCompany(company)} className={companyActive === index ? "active" : ""}><span className="combo-avatar">{company.name[0]}</span><span><strong>{company.name}</strong>{company.city && <small>{company.city}</small>}</span><i>Actif</i></button>)}
          {companyText.trim().length >= 2 && !companySearch.isFetching && companyResults.length === 0 && <p>Aucune entreprise correspondante.</p>}
          {companyText.trim().length >= 2 && !companyExact && <button type="button" className="combo-create" disabled={companyCreation.isPending} onMouseDown={(event) => event.preventDefault()} onClick={() => companyCreation.mutate()}>＋ Créer l’entreprise « {companyText.trim()} »</button>}
        </div>}
      </> : <article className="selected-company-card"><span className="combo-avatar">{selectedCompany.name[0]}</span><div><small>Entreprise sélectionnée</small><strong>{selectedCompany.name}</strong>{selectedCompany.city && <p>{selectedCompany.city}</p>}</div><button type="button" onClick={() => { setSelectedCompany(null); setCompanyText(""); setValue("company_id", ""); setValue("primary_contact_id", ""); }}>Changer</button><button type="button" onClick={() => { setSelectedCompany(null); setCompanyText(""); setValue("company_id", ""); setValue("primary_contact_id", ""); }}>Effacer</button></article>}
      {errors.company_id && <span className="field-error">{errors.company_id.message}</span>}
    </div>

    <div className="case-contact-field" ref={contactRef}>
      <label>Personne à contacter</label>
      <button type="button" role="combobox" aria-label="Personne à contacter" aria-expanded={contactOpen} aria-controls="contact-options" disabled={!companyId} className="field combo-button" onClick={() => setContactOpen((value) => !value)}>{selectedContact?.full_name ?? (companyId ? "Choisir une personne (facultatif)" : "Sélectionnez d’abord une entreprise")}<span>⌄</span></button>
      {contactOpen && companyId && <div className="combobox-menu contact-menu" id="contact-options" role="listbox">
        <input aria-label="Rechercher une personne" className="field" value={contactSearch} onChange={(event) => setContactSearch(event.target.value)} placeholder="Nom, email ou téléphone…" autoFocus />
        {visibleContacts.map((contact) => <button type="button" role="option" aria-selected={contact.id === contactId} key={contact.id} onClick={() => { setValue("primary_contact_id", contact.id); setContactOpen(false); }}><span className="combo-avatar">{contact.full_name[0]}</span><span><strong>{contact.full_name}</strong><small>{[contact.job_title, contact.phone || contact.email].filter(Boolean).join(" · ")}</small></span>{contact.is_primary && <i>Contact principal</i>}</button>)}
        {contacts.length === 0 && <p>Aucune personne enregistrée pour cette entreprise.</p>}
        <button type="button" className="combo-create" onClick={() => { setContactOpen(false); setContactModal(true); }}>＋ Ajouter une nouvelle personne</button>
      </div>}
    </div>

    <label className="case-theme-field">Thème de la formation <em>*</em>
      <select aria-label="Thème" {...register("theme")} className="field" defaultValue={theme} disabled={trainingCatalog.isPending}>
        <option value="">{trainingCatalog.isPending ? "Chargement du catalogue…" : "Sélectionner une formation du catalogue"}</option>
        {catalogIsFamilyList
          ? catalogByCategory.map(([, items]) => <option key={items[0]} value={items[0]}>{items[0]}</option>)
          : catalogByCategory.map(([category, items]) => <optgroup key={category} label={category}>{items.map((item) => <option key={item} value={item}>{item}</option>)}</optgroup>)}
      </select>
      <small className="form-help">Le thème est sélectionné exclusivement depuis le catalogue de formations.</small>
      {trainingCatalog.isError && <span className="field-error" role="alert">Impossible de charger le catalogue de formations.</span>}
      {errors.theme && <span className="field-error">{errors.theme.message}</span>}
    </label>

    <label className="case-description-field">Description du besoin <span className="optional-label">(facultatif)</span><textarea aria-label="Description du besoin" {...register("description")} rows={5} maxLength={1000} placeholder="Objectif général et contexte de la demande…" className="field" /><small>{description?.length ?? 0}/1000</small>{errors.description && <span className="field-error">{errors.description.message}</span>}</label>
    {contactModal && <div className="modal-backdrop" role="presentation"><section role="dialog" aria-modal="true" aria-labelledby="contact-modal-title" className="quick-contact-modal"><h2 id="contact-modal-title">Ajouter une personne</h2><label>Nom complet *<input className="field" value={contactDraft.full_name} onChange={(event) => setContactDraft((current) => ({ ...current, full_name: event.target.value }))} /></label><label>Téléphone<input className="field" value={contactDraft.phone} onChange={(event) => setContactDraft((current) => ({ ...current, phone: event.target.value }))} /></label><label>Email<input type="email" className="field" value={contactDraft.email} onChange={(event) => setContactDraft((current) => ({ ...current, email: event.target.value }))} /></label><div><button type="button" className="btn btn-secondary" onClick={() => setContactModal(false)}>Annuler</button><button type="button" className="btn btn-primary" disabled={!contactDraft.full_name.trim() || contactCreation.isPending} onClick={() => contactCreation.mutate()}>{contactCreation.isPending ? "Ajout en cours…" : "Ajouter la personne"}</button></div></section></div>}
    {actionError && <p className="field-error form-api-error" role="alert">{actionError instanceof ApiError ? actionError.message : "L’action a échoué."}</p>}
    <div className="case-form-actions"><WorkflowActionBar primary={<button type="submit" aria-label={submitLabel === "Créer le dossier et continuer" ? "Créer le dossier" : submitLabel} className="btn btn-primary" disabled={pending || !formReady}>{pending ? "Création en cours…" : submitLabel}</button>} /></div>
  </form>;
}
