package com.trainflow.trainer.dto;
import java.math.BigDecimal; import java.time.Instant; import java.util.UUID;
public record TrainerResponse(UUID id,String firstName,String lastName,String fullName,String email,String phone,String mobilePhone,String birthDate,String birthPlace,String address,String company,String employerAddress,String jobTitle,Integer yearsExperience,BigDecimal hourlyRate,BigDecimal dailyRate,String city,String country,String linkedinUrl,String website,String notes,UUID cvId,boolean isActive,Instant createdAt,Instant updatedAt) {}
