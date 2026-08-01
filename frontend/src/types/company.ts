export type Contact = {
  id: string;
  company_id: string;
  full_name: string;
  email: string | null;
  phone: string | null;
  job_title: string | null;
  is_primary: boolean;
  created_at: string;
  updated_at: string;
};

export type Company = {
  id: string;
  name: string;
  address: string | null;
  city: string | null;
  postal_code: string | null;
  country: string | null;
  tax_identifier: string | null;
  website: string | null;
  notes: string | null;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
};

export type CompanyDetail = Company & { contacts: Contact[] };
export type CompanyListItem = Company & { primary_contact: Contact | null };
export type CompanyList = {
  items: CompanyListItem[];
  total: number;
  page: number;
  page_size: number;
};

export type CompanyInput = {
  name: string;
  address?: string;
  city?: string;
  postal_code?: string;
  country?: string;
  tax_identifier?: string;
  website?: string;
  notes?: string;
};

export type ContactInput = {
  full_name: string;
  email?: string;
  phone?: string;
  job_title?: string;
  is_primary: boolean;
};
