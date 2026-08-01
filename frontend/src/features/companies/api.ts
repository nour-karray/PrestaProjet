import { apiRequest } from "@/lib/api";
import type {
  CompanyDetail,
  CompanyInput,
  CompanyList,
  Contact,
  ContactInput,
} from "@/types/company";

export type CompanyFilters = {
  search?: string;
  city?: string;
  country?: string;
  page?: number;
  pageSize?: number;
  includeArchived?: boolean;
};

export function getCompanies(filters: CompanyFilters): Promise<CompanyList> {
  const params = new URLSearchParams();
  if (filters.search) params.set("search", filters.search);
  if (filters.city) params.set("city", filters.city);
  if (filters.country) params.set("country", filters.country);
  if (filters.page) params.set("page", String(filters.page));
  if (filters.pageSize) params.set("page_size", String(filters.pageSize));
  if (filters.includeArchived) params.set("include_archived", "true");
  return apiRequest(`/api/companies?${params.toString()}`);
}

export function getCompany(id: string): Promise<CompanyDetail> {
  return apiRequest(`/api/companies/${id}`);
}

export function createCompany(payload: CompanyInput): Promise<CompanyDetail> {
  return apiRequest("/api/companies", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateCompany(
  id: string,
  payload: CompanyInput,
): Promise<CompanyDetail> {
  return apiRequest(`/api/companies/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function archiveCompany(id: string): Promise<{ message: string }> {
  return apiRequest(`/api/companies/${id}`, { method: "DELETE" });
}

export function createContact(
  companyId: string,
  payload: ContactInput,
): Promise<Contact> {
  return apiRequest(`/api/companies/${companyId}/contacts`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateContact(
  id: string,
  payload: Partial<ContactInput>,
): Promise<Contact> {
  return apiRequest(`/api/contacts/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function deleteContact(id: string): Promise<{ message: string }> {
  return apiRequest(`/api/contacts/${id}`, { method: "DELETE" });
}
