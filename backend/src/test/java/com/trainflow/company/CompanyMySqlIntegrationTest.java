package com.trainflow.company;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.transaction.annotation.Transactional;
import org.testcontainers.containers.MySQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

@Testcontainers(disabledWithoutDocker = true)
@SpringBootTest
@Transactional
class CompanyMySqlIntegrationTest {
    @Container
    static MySQLContainer<?> mysql = new MySQLContainer<>("mysql:8.4")
            .withInitScript("company-mysql-test-schema.sql");

    @DynamicPropertySource
    static void database(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", mysql::getJdbcUrl);
        registry.add("spring.datasource.username", mysql::getUsername);
        registry.add("spring.datasource.password", mysql::getPassword);
        registry.add("spring.jpa.hibernate.ddl-auto", () -> "validate");
    }

    @Autowired CompanyService service;

    @Test
    void persistsCompanyAndContactAgainstMySql() {
        CompanyResponse company = service.create(new CompanyCreateRequest("Alpha Conseil", null, "Tunis", null, "Tunisie", null, null, null));
        service.createContact(company.id(), new ContactCreateRequest("Amina Test", "amina@example.test", null, "Direction", true));
        assertEquals(1, service.listContacts(company.id()).size());
        assertEquals("Amina Test", service.get(company.id()).contacts().getFirst().fullName());
    }
}
