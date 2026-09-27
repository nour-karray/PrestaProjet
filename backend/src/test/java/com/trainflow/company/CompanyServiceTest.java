package com.trainflow.company;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

import com.trainflow.shared.error.ApiError;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

@ExtendWith(MockitoExtension.class)
class CompanyServiceTest {
    @Mock CompanyRepository companies;
    @Mock CompanyContactRepository contacts;
    CompanyService service;

    @BeforeEach void setUp() { service = new CompanyService(companies, contacts); }

    @Test
    void normalizesCompanyNameLikeFastApi() {
        when(companies.existsByNameIgnoreCase("Alpha Conseil")).thenReturn(false);
        when(companies.saveAndFlush(any())).thenAnswer(invocation -> invocation.getArgument(0));
        when(contacts.findByCompanyIdOrderByPrimaryDescFullNameAsc(any())).thenReturn(List.of());
        CompanyResponse response = service.create(new CompanyCreateRequest("  Alpha   Conseil  ", null, " Tunis ", null, "Tunisie", null, null, null));
        assertEquals("Alpha Conseil", response.name());
        assertEquals("Tunis", response.city());
    }

    @Test
    void rejectsDuplicateNameIgnoringCase() {
        when(companies.existsByNameIgnoreCase("alpha conseil")).thenReturn(true);
        ApiError error = assertThrows(ApiError.class, () -> service.create(
                new CompanyCreateRequest("alpha conseil", null, null, null, null, null, null, null)));
        assertEquals("COMPANY_NAME_CONFLICT", error.getCode());
        assertEquals(409, error.getStatus().value());
    }

    @Test
    void preservesNotFoundErrorContract() {
        when(companies.findById(any())).thenReturn(Optional.empty());
        ApiError error = assertThrows(ApiError.class, () -> service.get(java.util.UUID.randomUUID()));
        assertEquals("COMPANY_NOT_FOUND", error.getCode());
        assertEquals("L’entreprise est introuvable.", error.getMessage());
    }
}
