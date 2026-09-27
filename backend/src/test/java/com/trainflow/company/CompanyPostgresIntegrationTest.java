package com.trainflow.company;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.transaction.annotation.Transactional;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

@Testcontainers(disabledWithoutDocker = true)
@SpringBootTest
@Transactional
class CompanyPostgresIntegrationTest {
    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16-alpine")
            .withInitScript("company-test-schema.sql");

    @DynamicPropertySource
    static void database(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
        registry.add("spring.jpa.hibernate.ddl-auto", () -> "validate");
    }

    @Autowired CompanyService service;

    @Test
    void persistsCompanyAndContactAgainstPostgres() {
        CompanyResponse company = service.create(new CompanyCreateRequest("Alpha Conseil", null, "Tunis", null, "Tunisie", null, null, null));
        service.createContact(company.id(), new ContactCreateRequest("Amina Test", "amina@example.test", null, "Direction", true));
        assertEquals(1, service.listContacts(company.id()).size());
        assertEquals("Amina Test", service.get(company.id()).contacts().getFirst().fullName());
    }
}
