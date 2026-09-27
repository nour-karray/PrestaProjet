package com.trainflow.company;

import jakarta.validation.Valid;
import java.util.List;
import java.util.UUID;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api")
public class CompanyController {
    private final CompanyService service;
    public CompanyController(CompanyService service) { this.service = service; }

    @GetMapping("/companies")
    CompanyListResponse list(@RequestParam(required = false) String search,
                             @RequestParam(required = false) String city,
                             @RequestParam(required = false) String country,
                             @RequestParam(name = "include_archived", defaultValue = "false") boolean includeArchived,
                             @RequestParam(defaultValue = "1") int page,
                             @RequestParam(name = "page_size", defaultValue = "10") int pageSize,
                             @RequestParam(name = "sort_by", defaultValue = "name") String sortBy,
                             @RequestParam(name = "sort_order", defaultValue = "asc") String sortOrder) {
        return service.list(search, city, country, includeArchived, page, pageSize, sortBy, sortOrder);
    }

    @PostMapping("/companies") @ResponseStatus(HttpStatus.CREATED)
    CompanyResponse create(@Valid @RequestBody CompanyCreateRequest request) { return service.create(request); }
    @GetMapping("/companies/{id}") CompanyResponse get(@PathVariable UUID id) { return service.get(id); }
    @PatchMapping("/companies/{id}") CompanyResponse update(@PathVariable UUID id, @Valid @RequestBody CompanyUpdateRequest request) { return service.update(id, request); }
    @DeleteMapping("/companies/{id}") MessageResponse archive(@PathVariable UUID id) { service.archive(id); return new MessageResponse("L’entreprise a été archivée."); }
    @GetMapping("/companies/{id}/contacts") List<ContactResponse> contacts(@PathVariable UUID id) { return service.listContacts(id); }
    @PostMapping("/companies/{id}/contacts") @ResponseStatus(HttpStatus.CREATED)
    ContactResponse createContact(@PathVariable UUID id, @Valid @RequestBody ContactCreateRequest request) { return service.createContact(id, request); }
    @PatchMapping("/contacts/{id}") ContactResponse updateContact(@PathVariable UUID id, @Valid @RequestBody ContactUpdateRequest request) { return service.updateContact(id, request); }
    @DeleteMapping("/contacts/{id}") MessageResponse deleteContact(@PathVariable UUID id) { service.deleteContact(id); return new MessageResponse("Le contact a été supprimé."); }
}
