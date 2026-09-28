package com.trainflow.trainingcase.dto; import jakarta.validation.constraints.*; import java.time.LocalDate; import java.util.UUID;
public record TrainingCaseRequest(@NotNull UUID companyId,UUID primaryContactId,@NotBlank @Size(max=250) String theme,String description,LocalDate desiredStartDate,LocalDate desiredEndDate) {}
