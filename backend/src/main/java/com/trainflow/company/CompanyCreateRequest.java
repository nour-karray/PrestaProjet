package com.trainflow.company;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record CompanyCreateRequest(
        @NotBlank @Size(max = 200) String name,
        @Size(max = 300) String address,
        @Size(max = 120) String city,
        @Size(max = 30) String postalCode,
        @Size(max = 120) String country,
        @Size(max = 80) String taxIdentifier,
        @Size(max = 300) String website,
        String notes) {}
