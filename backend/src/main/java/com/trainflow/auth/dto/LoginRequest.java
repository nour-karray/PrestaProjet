package com.trainflow.auth.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

public record LoginRequest(
        @NotBlank @Size(min = 5, max = 320)
        @Pattern(regexp = "^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$", message = "L’adresse email est invalide.")
        String email,
        @NotBlank @Size(min = 8, max = 128) String password) {
    public LoginRequest {
        if (email != null) email = email.strip().toLowerCase(java.util.Locale.ROOT);
    }
}
