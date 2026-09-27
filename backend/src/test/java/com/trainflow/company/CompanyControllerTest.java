package com.trainflow.company;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.trainflow.shared.error.GlobalExceptionHandler;
import java.time.Instant;
import java.util.List;
import java.util.UUID;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

@WebMvcTest(CompanyController.class)
@Import(GlobalExceptionHandler.class)
class CompanyControllerTest {
    @Autowired MockMvc mvc;
    @MockitoBean CompanyService service;

    @Test
    void returnsSnakeCasePaginationContract() throws Exception {
        UUID id = UUID.randomUUID();
        Instant now = Instant.parse("2026-09-27T12:00:00Z");
        ContactResponse primary = new ContactResponse(UUID.randomUUID(), id, "Amina Test", "amina@example.test", null, null, true, now, now);
        CompanyListItem item = new CompanyListItem(id, "Alpha Conseil", null, "Tunis", null, "Tunisie", null, null, null, false, now, now, primary);
        when(service.list(null, null, null, false, 1, 10, "name", "asc"))
                .thenReturn(new CompanyListResponse(List.of(item), 1, 1, 10));

        mvc.perform(get("/api/companies"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.page_size").value(10))
                .andExpect(jsonPath("$.items[0].is_archived").value(false))
                .andExpect(jsonPath("$.items[0].primary_contact.full_name").value("Amina Test"));
    }

    @Test
    void acceptsFastApiSnakeCaseQueryParameters() throws Exception {
        when(service.list(null, null, null, true, 2, 25, "created_at", "desc"))
                .thenReturn(new CompanyListResponse(List.of(), 0, 2, 25));
        mvc.perform(get("/api/companies")
                        .param("include_archived", "true")
                        .param("page", "2").param("page_size", "25")
                        .param("sort_by", "created_at").param("sort_order", "desc"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.page").value(2))
                .andExpect(jsonPath("$.page_size").value(25));
    }

    @Test
    void createsCompanyWithExistingJsonContract() throws Exception {
        UUID id = UUID.randomUUID();
        Instant now = Instant.parse("2026-09-27T12:00:00Z");
        when(service.create(any())).thenReturn(new CompanyResponse(id, "Alpha Conseil", null, "Tunis", null, "Tunisie", null, null, null, false, now, now, List.of()));
        mvc.perform(post("/api/companies").contentType(MediaType.APPLICATION_JSON)
                        .content("{\"name\":\"Alpha Conseil\",\"city\":\"Tunis\",\"country\":\"Tunisie\"}"))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.name").value("Alpha Conseil"))
                .andExpect(jsonPath("$.is_archived").value(false))
                .andExpect(jsonPath("$.contacts").isArray());
    }

    @Test
    void keepsFastApiStyleValidationEnvelope() throws Exception {
        mvc.perform(post("/api/companies").contentType(MediaType.APPLICATION_JSON).content("{\"name\":\"   \"}"))
                .andExpect(status().isUnprocessableEntity())
                .andExpect(jsonPath("$.code").value("VALIDATION_ERROR"))
                .andExpect(jsonPath("$.message").value("Les données envoyées sont invalides."))
                .andExpect(jsonPath("$.details").isArray());
    }
}
