package com.trainflow.company;

import java.time.Instant;
import java.util.List;
import java.util.UUID;

public record CompanyResponse(
        UUID id, String name, String address, String city, String postalCode,
        String country, String taxIdentifier, String website, String notes,
        boolean isArchived, Instant createdAt, Instant updatedAt,
        List<ContactResponse> contacts) {}
