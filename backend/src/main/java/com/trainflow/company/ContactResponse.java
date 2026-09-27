package com.trainflow.company;

import java.time.Instant;
import java.util.UUID;

public record ContactResponse(
        UUID id, UUID companyId, String fullName, String email, String phone,
        String jobTitle, boolean isPrimary, Instant createdAt, Instant updatedAt) {}
