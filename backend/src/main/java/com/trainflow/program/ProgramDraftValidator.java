package com.trainflow.program;

import com.trainflow.shared.error.ApiError;
import java.util.*;
import java.util.stream.Collectors;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;

@Component
class ProgramDraftValidator {
    ValidatedProgramDraft validate(Map<String, Object> raw, ProgramGenerationInput input) {
        if (raw == null || raw.isEmpty()) throw invalid("La réponse IA est vide.");
        String title = required(raw.get("title"), "title");
        int durationDays = positive(raw.get("duration_days"), "duration_days");
        if (durationDays != input.plannedDaysCount()) throw invalid("duration_days ne correspond pas au besoin.");
        if (!(raw.get("days") instanceof List<?> rawDays) || rawDays.isEmpty()) throw invalid("days est obligatoire.");
        if (rawDays.size() != durationDays) throw invalid("Le nombre de journées est incohérent.");

        List<ValidatedProgramDraft.Day> days = new ArrayList<>();
        Set<Integer> dayNumbers = new HashSet<>();
        int totalMinutes = 0;
        for (Object rawDay : rawDays) {
            if (!(rawDay instanceof Map<?, ?> day)) throw invalid("Une journée est invalide.");
            int dayNumber = positive(day.get("day_number"), "day_number");
            if (!dayNumbers.add(dayNumber)) throw invalid("Les numéros de journée doivent être uniques.");
            String dayTitle = required(day.get("title"), "days.title");
            if (!(day.get("contents") instanceof List<?> contents) || contents.isEmpty()) throw invalid("Chaque journée doit contenir des modules.");
            List<ValidatedProgramDraft.Item> items = new ArrayList<>();
            Set<Integer> indexes = new HashSet<>();
            for (Object rawItem : contents) {
                if (!(rawItem instanceof Map<?, ?> item)) throw invalid("Un module est invalide.");
                int orderIndex = positive(item.get("order_index"), "order_index");
                if (!indexes.add(orderIndex)) throw invalid("Les positions des modules doivent être uniques.");
                String itemTitle = required(item.get("title"), "contents.title");
                int theory = nonNegative(item.get("theory_minutes"), "theory_minutes");
                int practice = nonNegative(item.get("practice_minutes"), "practice_minutes");
                if (theory + practice <= 0) throw invalid("La durée d’un module doit être positive.");
                if (!(item.get("methods") instanceof List<?> methods) || methods.isEmpty()) throw invalid("method_type est obligatoire.");
                Set<PedagogicalMethod> parsedMethods = new LinkedHashSet<>();
                for (Object method : methods) {
                    try { parsedMethods.add(PedagogicalMethod.valueOf(String.valueOf(method))); }
                    catch (IllegalArgumentException error) { throw invalid("Méthode pédagogique inconnue : " + method); }
                }
                String content = item.get("concepts") instanceof List<?> concepts
                        ? concepts.stream().map(String::valueOf).filter(value -> !value.isBlank()).collect(Collectors.joining("\n"))
                        : null;
                items.add(new ValidatedProgramDraft.Item(orderIndex, itemTitle, content, theory, practice, parsedMethods));
                totalMinutes += theory + practice;
            }
            List<Integer> expectedIndexes = java.util.stream.IntStream.rangeClosed(1, items.size()).boxed().toList();
            if (!indexes.containsAll(expectedIndexes)) throw invalid("L’ordre des modules est invalide.");
            days.add(new ValidatedProgramDraft.Day(dayNumber, dayTitle, items.stream().sorted(Comparator.comparingInt(ValidatedProgramDraft.Item::orderIndex)).toList()));
        }
        List<Integer> expectedDays = java.util.stream.IntStream.rangeClosed(1, durationDays).boxed().toList();
        if (!dayNumbers.containsAll(expectedDays)) throw invalid("L’ordre des journées est invalide.");
        if (totalMinutes != input.totalDurationMinutes()) throw new ApiError(HttpStatus.BAD_GATEWAY,
                "LLM_INVALID_RESPONSE", "La durée du programme généré est incohérente.",
                Map.of("expected_minutes", input.totalDurationMinutes(), "actual_minutes", totalMinutes));
        return new ValidatedProgramDraft(title, text(raw.get("general_objectives")), text(raw.get("prerequisites")),
                text(raw.get("evaluation_method")), days.stream().sorted(Comparator.comparingInt(ValidatedProgramDraft.Day::dayNumber)).toList());
    }

    private int positive(Object value, String field) { int parsed = integer(value, field); if (parsed <= 0) throw invalid(field + " doit être positif."); return parsed; }
    private int nonNegative(Object value, String field) { int parsed = integer(value, field); if (parsed < 0) throw invalid(field + " ne peut pas être négatif."); return parsed; }
    private int integer(Object value, String field) { if (value instanceof Number number) return number.intValue(); throw invalid(field + " est invalide."); }
    private String required(Object value, String field) { String parsed = text(value); if (parsed == null) throw invalid(field + " est obligatoire."); return parsed; }
    private String text(Object value) { if (value == null) return null; String parsed = String.valueOf(value).trim(); return parsed.isEmpty() ? null : parsed; }
    private ApiError invalid(String message) { return new ApiError(HttpStatus.BAD_GATEWAY, "LLM_INVALID_RESPONSE", message); }
}
