package com.trainflow.company;

import com.trainflow.shared.error.ApiError;
import java.util.List;
import java.util.Locale;
import java.util.UUID;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional(readOnly = true)
public class CompanyService {
    private final CompanyRepository companies;
    private final CompanyContactRepository contacts;

    public CompanyService(CompanyRepository companies, CompanyContactRepository contacts) {
        this.companies = companies;
        this.contacts = contacts;
    }

    public CompanyListResponse list(String search, String city, String country, boolean includeArchived,
                                    int page, int pageSize, String sortBy, String sortOrder) {
        if (page < 1 || pageSize < 1 || pageSize > 100
                || !(sortBy.equals("name") || sortBy.equals("created_at"))
                || !(sortOrder.equals("asc") || sortOrder.equals("desc"))) {
            throw new ApiError(HttpStatus.UNPROCESSABLE_ENTITY, "VALIDATION_ERROR", "Les paramètres de pagination ou de tri sont invalides.");
        }
        Specification<Company> specification = Specification.unrestricted();
        if (!includeArchived) specification = specification.and((root, query, cb) -> cb.isFalse(root.get("archived")));
        specification = addContains(specification, "name", search);
        specification = addContains(specification, "city", city);
        specification = addContains(specification, "country", country);
        String property = sortBy.equals("created_at") ? "createdAt" : "name";
        Sort sort = Sort.by(sortOrder.equals("desc") ? Sort.Direction.DESC : Sort.Direction.ASC, property);
        Page<Company> result = companies.findAll(specification, PageRequest.of(page - 1, pageSize, sort));
        List<CompanyListItem> items = result.getContent().stream().map(company -> new CompanyListItem(
                company.getId(), company.getName(), company.getAddress(), company.getCity(), company.getPostalCode(),
                company.getCountry(), company.getTaxIdentifier(), company.getWebsite(), company.getNotes(),
                company.isArchived(), company.getCreatedAt(), company.getUpdatedAt(),
                contacts.findFirstByCompanyIdAndPrimaryTrue(company.getId()).map(CompanyService::contactResponse).orElse(null)
        )).toList();
        return new CompanyListResponse(items, result.getTotalElements(), page, pageSize);
    }

    private Specification<Company> addContains(Specification<Company> base, String field, String value) {
        String cleaned = clean(value);
        if (cleaned == null) return base;
        String pattern = "%" + cleaned.toLowerCase(Locale.ROOT) + "%";
        return base.and((root, query, cb) -> cb.like(cb.lower(root.get(field)), pattern));
    }

    public CompanyResponse get(UUID id) { return companyResponse(requireCompany(id)); }

    @Transactional
    public CompanyResponse create(CompanyCreateRequest request) {
        String name = required(request.name());
        ensureNameAvailable(name, null);
        Company company = new Company(name);
        apply(company, request.address(), request.city(), request.postalCode(), request.country(),
                request.taxIdentifier(), request.website(), request.notes());
        return companyResponse(companies.saveAndFlush(company));
    }

    @Transactional
    public CompanyResponse update(UUID id, CompanyUpdateRequest request) {
        Company company = requireCompany(id);
        if (request.has("name")) {
            String name = required(request.getName());
            ensureNameAvailable(name, id);
            company.setName(name);
        }
        if (request.has("address")) company.setAddress(clean(request.getAddress()));
        if (request.has("city")) company.setCity(clean(request.getCity()));
        if (request.has("postalCode")) company.setPostalCode(clean(request.getPostalCode()));
        if (request.has("country")) company.setCountry(clean(request.getCountry()));
        if (request.has("taxIdentifier")) company.setTaxIdentifier(clean(request.getTaxIdentifier()));
        if (request.has("website")) company.setWebsite(clean(request.getWebsite()));
        if (request.has("notes")) company.setNotes(clean(request.getNotes()));
        return companyResponse(companies.saveAndFlush(company));
    }

    @Transactional
    public void archive(UUID id) {
        Company company = requireCompany(id);
        company.setArchived(true);
        companies.save(company);
    }

    public List<ContactResponse> listContacts(UUID companyId) {
        requireCompany(companyId);
        return contacts.findByCompanyIdOrderByPrimaryDescFullNameAsc(companyId).stream()
                .map(CompanyService::contactResponse).toList();
    }

    @Transactional
    public ContactResponse createContact(UUID companyId, ContactCreateRequest request) {
        Company company = requireCompany(companyId);
        String fullName = required(request.fullName());
        if (request.isPrimary()) contacts.clearPrimary(companyId);
        CompanyContact contact = new CompanyContact(company, fullName);
        contact.setEmail(email(request.email()));
        contact.setPhone(clean(request.phone()));
        contact.setJobTitle(clean(request.jobTitle()));
        contact.setPrimary(request.isPrimary());
        return contactResponse(contacts.saveAndFlush(contact));
    }

    @Transactional
    public ContactResponse updateContact(UUID id, ContactUpdateRequest request) {
        CompanyContact contact = requireContact(id);
        if (request.has("isPrimary") && Boolean.TRUE.equals(request.getIsPrimary())) {
            contacts.clearPrimaryExcept(contact.getCompany().getId(), contact.getId());
        }
        if (request.has("fullName")) contact.setFullName(required(request.getFullName()));
        if (request.has("email")) contact.setEmail(email(request.getEmail()));
        if (request.has("phone")) contact.setPhone(clean(request.getPhone()));
        if (request.has("jobTitle")) contact.setJobTitle(clean(request.getJobTitle()));
        if (request.has("isPrimary")) contact.setPrimary(Boolean.TRUE.equals(request.getIsPrimary()));
        return contactResponse(contacts.saveAndFlush(contact));
    }

    @Transactional
    public void deleteContact(UUID id) { contacts.delete(requireContact(id)); }

    private Company requireCompany(UUID id) {
        return companies.findById(id).orElseThrow(() -> new ApiError(
                HttpStatus.NOT_FOUND, "COMPANY_NOT_FOUND", "L’entreprise est introuvable."));
    }

    private CompanyContact requireContact(UUID id) {
        return contacts.findById(id).orElseThrow(() -> new ApiError(
                HttpStatus.NOT_FOUND, "CONTACT_NOT_FOUND", "Le contact est introuvable."));
    }

    private void ensureNameAvailable(String name, UUID excludedId) {
        boolean exists = excludedId == null ? companies.existsByNameIgnoreCase(name)
                : companies.existsByNameIgnoreCaseAndIdNot(name, excludedId);
        if (exists) throw new ApiError(HttpStatus.CONFLICT, "COMPANY_NAME_CONFLICT", "Une entreprise portant ce nom existe déjà.");
    }

    private void apply(Company company, String address, String city, String postalCode, String country,
                       String taxIdentifier, String website, String notes) {
        company.setAddress(clean(address)); company.setCity(clean(city)); company.setPostalCode(clean(postalCode));
        company.setCountry(clean(country)); company.setTaxIdentifier(clean(taxIdentifier));
        company.setWebsite(clean(website)); company.setNotes(clean(notes));
    }

    private static String required(String value) {
        String cleaned = clean(value);
        if (cleaned == null) throw new ApiError(HttpStatus.UNPROCESSABLE_ENTITY, "VALIDATION_ERROR", "Les données envoyées sont invalides.");
        return cleaned;
    }
    private static String clean(String value) {
        if (value == null) return null;
        String cleaned = value.trim().replaceAll("\\s+", " ");
        return cleaned.isEmpty() ? null : cleaned;
    }
    private static String email(String value) {
        String cleaned = clean(value);
        return cleaned == null ? null : cleaned.toLowerCase(Locale.ROOT);
    }
    private static ContactResponse contactResponse(CompanyContact contact) {
        return new ContactResponse(contact.getId(), contact.getCompany().getId(), contact.getFullName(), contact.getEmail(),
                contact.getPhone(), contact.getJobTitle(), contact.isPrimary(), contact.getCreatedAt(), contact.getUpdatedAt());
    }
    private CompanyResponse companyResponse(Company company) {
        List<ContactResponse> companyContacts = contacts.findByCompanyIdOrderByPrimaryDescFullNameAsc(company.getId()).stream()
                .map(CompanyService::contactResponse).toList();
        return new CompanyResponse(company.getId(), company.getName(), company.getAddress(), company.getCity(),
                company.getPostalCode(), company.getCountry(), company.getTaxIdentifier(), company.getWebsite(),
                company.getNotes(), company.isArchived(), company.getCreatedAt(), company.getUpdatedAt(), companyContacts);
    }
}
