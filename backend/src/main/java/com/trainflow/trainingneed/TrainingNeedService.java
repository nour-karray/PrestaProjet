package com.trainflow.trainingneed;

import com.trainflow.shared.error.ApiError;
import com.trainflow.trainingcase.*;
import java.time.*;
import java.util.*;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.http.HttpStatus;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class TrainingNeedService {
    private final TrainingNeedRepository needs;
    private final TrainingCaseRepository cases;
    private final ActivityRepository activities;

    public TrainingNeedService(TrainingNeedRepository needs, TrainingCaseRepository cases, ActivityRepository activities) {
        this.needs = needs; this.cases = cases; this.activities = activities;
    }

    @Transactional(readOnly = true)
    public TrainingNeedResponse get(UUID caseId) {
        caseEntity(caseId);
        return response(needs.findByTrainingCaseId(caseId).orElseThrow(() -> notFound()));
    }

    @Transactional
    public TrainingNeedResponse create(UUID caseId, TrainingNeedRequest request) {
        TrainingCase trainingCase = mutableCase(caseId);
        ensureAccessible(trainingCase);
        if (needs.findByTrainingCaseId(caseId).isPresent()) throw conflict("TRAINING_NEED_ALREADY_EXISTS", "Un besoin client existe déjà pour ce dossier.");
        validatePeriod(request.desiredStartDate(), request.desiredEndDate(), request.plannedDaysCount());
        TrainingNeed need = new TrainingNeed(caseId); apply(need, request);
        try { needs.saveAndFlush(need); }
        catch (DataIntegrityViolationException error) { throw conflict("TRAINING_NEED_ALREADY_EXISTS", "Un besoin client existe déjà pour ce dossier."); }
        TrainingCaseStatus previous = trainingCase.getStatus();
        if (previous == TrainingCaseStatus.FORMATEUR_ACCEPTE) trainingCase.setStatus(TrainingCaseStatus.BESOIN_A_COMPLETER);
        log(trainingCase, need, "TrainingNeedCreated", previous, trainingCase.getStatus(), Map.of());
        return response(need);
    }

    @Transactional
    public TrainingNeedResponse update(UUID caseId, TrainingNeedRequest request) {
        TrainingCase trainingCase = mutableCase(caseId);
        ensureAccessible(trainingCase);
        TrainingNeed need = needs.locked(caseId).orElseThrow(() -> notFound());
        if (need.isValidated()) throw conflict("TRAINING_NEED_ALREADY_VALIDATED", "Un besoin validé ne peut plus être modifié.");
        validatePeriod(request.desiredStartDate(), request.desiredEndDate(), request.plannedDaysCount());
        apply(need, request);
        log(trainingCase, need, "TrainingNeedUpdated", trainingCase.getStatus(), trainingCase.getStatus(), Map.of());
        return response(need);
    }

    @Transactional
    public TrainingNeedResponse validate(UUID caseId) {
        TrainingCase trainingCase = mutableCase(caseId);
        TrainingNeed need = needs.locked(caseId).orElseThrow(() -> notFound());
        if (need.isValidated()) throw conflict("TRAINING_NEED_ALREADY_VALIDATED", "Ce besoin client est déjà validé.");
        if (trainingCase.getStatus() != TrainingCaseStatus.BESOIN_A_COMPLETER) throw conflict("INVALID_TRAINING_CASE_STATUS", "Le dossier n’est pas à l’étape de validation du besoin.");
        validateComplete(need);
        TrainingCaseStatus previous = trainingCase.getStatus();
        need.setValidated(true); need.setValidatedAt(Instant.now()); trainingCase.setStatus(TrainingCaseStatus.BESOIN_COMPLETE);
        log(trainingCase, need, "TrainingNeedValidated", previous, trainingCase.getStatus(), Map.of());
        return response(need);
    }

    private void apply(TrainingNeed n, TrainingNeedRequest r) {
        n.setTargetAudience(clean(r.targetAudience())); n.setLevel(r.level()); n.setLocation(clean(r.location())); n.setParticipantCount(r.participantCount()); n.setDeliveryMode(r.deliveryMode()); n.setDurationHours(r.durationHours()); n.setPlannedDaysCount(r.plannedDaysCount()); n.setObjectives(clean(r.objectives())); n.setDesiredStartDate(r.desiredStartDate()); n.setDesiredEndDate(r.desiredEndDate()); n.setConstraints(clean(r.constraints()));
    }
    private void validateComplete(TrainingNeed n) {
        List<String> missing = new ArrayList<>();
        if (blank(n.getTargetAudience())) missing.add("target_audience"); if (n.getLevel()==null) missing.add("level"); if (blank(n.getLocation())) missing.add("location"); if (n.getParticipantCount()==null) missing.add("participant_count"); if (n.getDeliveryMode()==null) missing.add("delivery_mode"); if (n.getDurationHours()==null) missing.add("duration_hours"); if (n.getPlannedDaysCount()==null) missing.add("planned_days_count"); if (blank(n.getObjectives())) missing.add("objectives"); if (n.getDesiredStartDate()==null) missing.add("desired_start_date"); if (n.getDesiredEndDate()==null) missing.add("desired_end_date");
        if (!missing.isEmpty()) throw new ApiError(HttpStatus.BAD_REQUEST, "TRAINING_NEED_INCOMPLETE", "Tous les champs obligatoires du besoin doivent être renseignés.", Map.of("missing_fields", missing));
        validatePeriod(n.getDesiredStartDate(), n.getDesiredEndDate(), n.getPlannedDaysCount());
    }
    private void validatePeriod(LocalDate start, LocalDate end, Integer days) {
        if (start != null && end != null && end.isBefore(start)) throw new ApiError(HttpStatus.BAD_REQUEST, "INVALID_TRAINING_NEED_PERIOD", "La date de fin doit être postérieure ou égale à la date de début.");
        if (start != null && end != null && days != null) { LocalDate expected = start.plusDays(days - 1L); if (!end.equals(expected)) throw new ApiError(HttpStatus.BAD_REQUEST, "INVALID_TRAINING_NEED_PLANNED_PERIOD", "La date de fin doit correspondre au début et au nombre de jours planifiés.", Map.of("expected_end_date", expected.toString())); }
    }
    private TrainingCase mutableCase(UUID id) { TrainingCase c = cases.locked(id).orElseThrow(() -> new ApiError(HttpStatus.NOT_FOUND,"TRAINING_CASE_NOT_FOUND","Le dossier est introuvable.")); if(c.isArchived()) throw conflict("ARCHIVED_TRAINING_CASE","Un dossier archivé ne peut pas être modifié."); if(c.getStatus()==TrainingCaseStatus.ANNULE) throw conflict("CANCELLED_TRAINING_CASE","Un dossier annulé ne peut pas être modifié."); return c; }
    private TrainingCase caseEntity(UUID id) { return cases.detailed(id).orElseThrow(() -> new ApiError(HttpStatus.NOT_FOUND,"TRAINING_CASE_NOT_FOUND","Le dossier est introuvable.")); }
    private void ensureAccessible(TrainingCase c) { if(c.getTrainer()==null) throw conflict("TRAINER_REQUIRED","Un formateur doit être affecté au dossier."); if(!Set.of(TrainingCaseStatus.FORMATEUR_ACCEPTE,TrainingCaseStatus.BESOIN_A_COMPLETER).contains(c.getStatus())) throw conflict("INVALID_TRAINING_CASE_STATUS","Le besoin client n’est pas accessible à cette étape du dossier."); }
    private void log(TrainingCase c, TrainingNeed n, String action, TrainingCaseStatus previous, TrainingCaseStatus next, Map<String,Object> extra) { Map<String,Object> details=new LinkedHashMap<>();details.put("training_case_id",c.getId().toString());details.put("training_need_id",n.getId().toString());details.put("previous_status",previous.name());details.put("new_status",next.name());details.putAll(extra);activities.save(new ActivityLog(admin(),c.getId(),action,"training_need",n.getId(),details)); }
    private UUID admin(){return UUID.fromString(SecurityContextHolder.getContext().getAuthentication().getName());}
    private TrainingNeedResponse response(TrainingNeed n){return new TrainingNeedResponse(n.getId(),n.getTrainingCaseId(),n.getTargetAudience(),n.getLevel(),n.getLocation(),n.getParticipantCount(),n.getDeliveryMode(),n.getDurationHours(),n.getPlannedDaysCount(),n.getObjectives(),n.getDesiredStartDate(),n.getDesiredEndDate(),n.getConstraints(),n.isValidated(),n.getValidatedAt(),n.getCreatedAt(),n.getUpdatedAt());}
    private ApiError notFound(){return new ApiError(HttpStatus.NOT_FOUND,"TRAINING_NEED_NOT_FOUND","Le besoin client est introuvable.");} private ApiError conflict(String c,String m){return new ApiError(HttpStatus.CONFLICT,c,m);} private String clean(String s){return s==null||s.trim().isEmpty()?null:s.trim();} private boolean blank(String s){return s==null||s.isBlank();}
}
