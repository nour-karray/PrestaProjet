package com.trainflow.program;

import java.util.List;
import java.util.Set;

record ValidatedProgramDraft(
        String title,
        String generalObjectives,
        String prerequisites,
        String evaluationMethod,
        List<Day> days) {
    record Day(int dayNumber, String title, List<Item> items) {}
    record Item(int orderIndex, String title, String content, int theoryMinutes,
                int practiceMinutes, Set<PedagogicalMethod> methods) {}
}
