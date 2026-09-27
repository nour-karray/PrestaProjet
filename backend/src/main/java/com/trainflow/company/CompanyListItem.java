package com.trainflow.company;

import java.time.Instant;
import java.util.UUID;

public record CompanyListItem(
        UUID id, String name, String address, String city, String postalCode,
        String country, String taxIdentifier, String website, String notes,
        boolean isArchived, Instant createdAt, Instant updatedAt,
        ContactResponse primaryContact) {}
