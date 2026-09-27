package com.trainflow.company;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

public record ContactCreateRequest(
        @NotBlank @Size(max = 200) String fullName,
        @Size(max = 320) @Pattern(regexp = "^$|^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$", message = "L'adresse email n'est pas valide.") String email,
        @Size(max = 50) String phone,
        @Size(max = 150) String jobTitle,
        boolean isPrimary) {}
