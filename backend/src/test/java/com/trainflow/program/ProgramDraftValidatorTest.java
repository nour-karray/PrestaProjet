package com.trainflow.program;

import static org.assertj.core.api.Assertions.*;
import com.trainflow.shared.error.ApiError;
import java.util.*;
import org.junit.jupiter.api.Test;

class ProgramDraftValidatorTest {
    private final ProgramDraftValidator validator = new ProgramDraftValidator();
    private final ProgramGenerationInput input = new ProgramGenerationInput(UUID.randomUUID(), "Cybersecurity",
            "Beginners", "Secure email", 1, 60,
            new ProgramGenerationInput.TrainerProfile("Amina", List.of(), List.of(), null, List.of()));

    @Test void acceptsExactCompleteDraft() {
        var result = validator.validate(valid("EXPOSE", 30, 30), input);
        assertThat(result.days()).hasSize(1);
        assertThat(result.days().getFirst().items().getFirst().methods()).containsExactly(PedagogicalMethod.EXPOSE);
    }

    @Test void rejectsUnknownPedagogicalMethod() {
        assertThatThrownBy(() -> validator.validate(valid("DISCUSSION", 30, 30), input))
                .isInstanceOf(ApiError.class).extracting("code").isEqualTo("LLM_INVALID_RESPONSE");
    }

    @Test void rejectsDurationMismatchBeforePersistence() {
        assertThatThrownBy(() -> validator.validate(valid("EXPOSE", 20, 20), input))
                .isInstanceOf(ApiError.class).extracting("code").isEqualTo("LLM_INVALID_RESPONSE");
    }

    @Test void rejectsMissingDays() {
        assertThatThrownBy(() -> validator.validate(Map.of("title", "Program", "duration_days", 1), input))
                .isInstanceOf(ApiError.class).extracting("code").isEqualTo("LLM_INVALID_RESPONSE");
    }

    @Test void rejectsEmptyResponse() {
        assertThatThrownBy(() -> validator.validate(Map.of(), input))
                .isInstanceOf(ApiError.class).extracting("code").isEqualTo("LLM_INVALID_RESPONSE");
    }

    @Test void rejectsItemWithoutPositiveDuration() {
        assertThatThrownBy(() -> validator.validate(valid("EXPOSE", 0, 0), input))
                .isInstanceOf(ApiError.class).extracting("code").isEqualTo("LLM_INVALID_RESPONSE");
    }

    private Map<String,Object> valid(String method,int theory,int practice) {
        return Map.of("title","Program","duration_days",1,"days",List.of(Map.of("day_number",1,
                "title","Day 1","contents",List.of(Map.of("order_index",1,"title","Threats",
                "concepts",List.of("Phishing"),"methods",List.of(method),
                "theory_minutes",theory,"practice_minutes",practice)))));
    }
}
