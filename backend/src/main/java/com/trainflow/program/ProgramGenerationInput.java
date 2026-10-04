package com.trainflow.program;

import java.util.List;
import java.util.UUID;

public record ProgramGenerationInput(
        UUID trainingCaseId,
        String theme,
        String targetAudience,
        String objectives,
        int plannedDaysCount,
        int totalDurationMinutes,
        TrainerProfile trainer) {
    public record TrainerProfile(
            String name,
            List<String> specialties,
            List<String> domains,
            Integer yearsOfExperience,
            List<String> certifications) {}
}
