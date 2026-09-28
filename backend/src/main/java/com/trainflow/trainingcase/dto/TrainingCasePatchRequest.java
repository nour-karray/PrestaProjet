package com.trainflow.trainingcase.dto; import jakarta.validation.constraints.Size; import java.time.LocalDate; import java.util.UUID;
public record TrainingCasePatchRequest(UUID companyId,UUID primaryContactId,@Size(min=1,max=250) String theme,String description,LocalDate desiredStartDate,LocalDate desiredEndDate) {}
