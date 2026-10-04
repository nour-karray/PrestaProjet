package com.trainflow.auth.dto;

import java.time.Instant;
import java.util.UUID;

public record AuthUserResponse(
        UUID id, String fullName, String email, boolean isActive,
        Instant createdAt, Instant lastLoginAt) {}
