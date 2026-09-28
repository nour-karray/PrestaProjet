package com.trainflow.trainer.dto;
import jakarta.validation.constraints.*; import java.math.BigDecimal;
public record TrainerRequest(String firstName,String lastName,@NotBlank @Size(max=200) String fullName,@Email @Size(max=320) String email,String phone,String mobilePhone,String birthDate,String birthPlace,String address,String company,String employerAddress,String jobTitle,@Min(0) @Max(80) Integer yearsExperience,@DecimalMin("0") BigDecimal hourlyRate,@DecimalMin("0") BigDecimal dailyRate,String city,String country,String linkedinUrl,String website,String notes) {}
